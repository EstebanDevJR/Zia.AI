from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.schemas import Article
from app.services.ddg import search_ddg
from app.services.observability import EXTERNAL_CALLS, log_event
from app.services.validator import validate_article

CATEGORY_QUERIES = {
    "research": "AI research OR machine learning paper OR arXiv",
    "industry": "AI company OR product launch OR funding OR partnership",
    "policy": "AI regulation OR policy OR government",
    "security": "AI security OR safety OR risk",
    "tools": "AI tools OR models OR platforms",
}

SAMPLE_NEWS = [
    Article(
        title="AI policy roadmap highlights safety priorities",
        description="Policy groups release a new framework for responsible AI adoption.",
        url="https://www.bbc.com/news/technology",
        source="bbc.com",
        published_at=datetime.utcnow(),
        image_url=None,
        category="policy",
        source_domain="bbc.com",
        trust_score=1.0,
        context=None,
    ),
    Article(
        title="New open research model sets efficiency records",
        description="Researchers introduce a lightweight model with strong benchmarks.",
        url="https://www.technologyreview.com/",
        source="technologyreview.com",
        published_at=datetime.utcnow(),
        image_url=None,
        category="research",
        source_domain="technologyreview.com",
        trust_score=1.0,
        context=None,
    ),
]


def _allowed_domains() -> list[str]:
    return [d.strip().lower() for d in settings.firecrawl_allowed_domains.split(",") if d.strip()]


def _domain_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def _is_allowed(url: str, allowed: list[str]) -> bool:
    domain = _domain_from_url(url)
    if not domain:
        return False
    return any(domain == allowed_domain or domain.endswith(f".{allowed_domain}") for allowed_domain in allowed)


def _is_https(url: str) -> bool:
    try:
        return urlparse(url).scheme.lower() == "https"
    except ValueError:
        return False


def _build_query(category: str | None, q: str | None) -> str:
    base = q or "artificial intelligence OR machine learning OR generative AI"
    if category and category in CATEGORY_QUERIES:
        return f"({base}) AND ({CATEGORY_QUERIES[category]})"
    return base


def _with_domain_filter(query: str, allowed: list[str]) -> str:
    if not allowed:
        return query
    sites = " OR ".join(f"site:{domain}" for domain in allowed)
    return f"({query}) AND ({sites})"


def _trust_score(domain: str, allowed: list[str]) -> float:
    if not allowed:
        return 0.7
    return 1.0 if any(domain == d or domain.endswith(f".{d}") for d in allowed) else 0.3


def fetch_news(
    category: str | None = None,
    q: str | None = None,
    lang: str | None = None,
    page: int = 1,
    page_size: int = 8,
) -> tuple[list[Article], bool]:
    items = _fetch_raw(category=category, q=q, lang=lang, limit=_limit_for_page(page, page_size))
    if not items:
        return [item for item in SAMPLE_NEWS if not category or item.category == category], False

    validation_query = q or category
    validated_items, has_more = _validate_and_slice(items, validation_query, page, page_size)
    return validated_items, has_more


def _fetch_raw(
    category: str | None,
    q: str | None,
    lang: str | None,
    limit: int,
) -> list[Article]:
    if not settings.firecrawl_api_key:
        return _fetch_ddg(category, q, lang, limit)

    allowed_domains = _allowed_domains()
    query = _build_query(category, q)
    query = _with_domain_filter(query, allowed_domains)

    payload: dict[str, Any] = {
        "query": query,
        "limit": limit,
        "sources": ["news"],
        "ignoreInvalidURLs": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(f"{settings.firecrawl_base}/search", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        EXTERNAL_CALLS.labels("firecrawl", "ok").inc()
    except httpx.HTTPError as exc:
        EXTERNAL_CALLS.labels("firecrawl", "error").inc()
        log_event("firecrawl_error", error=str(exc))
        return _fetch_ddg(category, q, lang, limit)

    results = _extract_results(data)
    items: list[Article] = []

    for result in results:
        url = result.get("url")
        if not url or not _is_https(url):
            continue
        if allowed_domains and not _is_allowed(url, allowed_domains):
            continue

        title = result.get("title") or "(Sin titulo)"
        description = result.get("description") or result.get("snippet")
        date_value = result.get("date") or result.get("publishedDate") or result.get("published_at")
        image_url = result.get("imageUrl") or result.get("image")

        domain = _domain_from_url(url)
        items.append(
            Article(
                title=title,
                description=description,
                url=url,
                source=domain,
                published_at=_safe_date(date_value),
                image_url=image_url,
                category=category,
                source_domain=domain,
                trust_score=_trust_score(domain, allowed_domains),
                context=None,
            )
        )

    return items


def _fetch_ddg(
    category: str | None,
    q: str | None,
    lang: str | None,
    limit: int,
) -> list[Article]:
    allowed_domains = _allowed_domains()
    query = _build_query(category, q)
    query = _with_domain_filter(query, allowed_domains)

    try:
        results = search_ddg(query=query, limit=limit, accept_language=lang)
        EXTERNAL_CALLS.labels("duckduckgo", "ok").inc()
    except httpx.HTTPError as exc:
        EXTERNAL_CALLS.labels("duckduckgo", "error").inc()
        log_event("ddg_error", error=str(exc))
        return []

    items: list[Article] = []
    for result in results:
        url = result.get("url")
        if not url or not _is_https(url):
            continue
        if allowed_domains and not _is_allowed(url, allowed_domains):
            continue

        domain = _domain_from_url(url)
        items.append(
            Article(
                title=result.get("title") or "(Sin titulo)",
                description=result.get("snippet"),
                url=url,
                source=domain,
                published_at=None,
                image_url=None,
                category=category,
                source_domain=domain,
                trust_score=_trust_score(domain, allowed_domains),
                context=None,
            )
        )

    return items


def _validate_and_slice(
    items: list[Article],
    query: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Article], bool]:
    if not settings.validation_enabled:
        for item in items:
            item.context = item.description
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], len(items) > end

    valid_items: list[Article] = []
    target_end = page * page_size
    validation_cap = max(settings.validation_max, target_end)
    processed = 0

    for item in items:
        processed += 1
        is_valid, context = validate_article(item, query)
        if is_valid:
            item.context = context or item.description
            valid_items.append(item)
        if len(valid_items) >= target_end:
            break
        if processed >= validation_cap:
            break

    start = (page - 1) * page_size
    end = start + page_size

    has_more = len(valid_items) > end or processed < len(items)
    return valid_items[start:end], has_more


def _limit_for_page(page: int, page_size: int) -> int:
    requested = page * page_size + 6
    return min(settings.news_max_limit, max(requested, settings.validation_max))


def _extract_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("news", "web", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _safe_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def new_tokens() -> tuple[str, str]:
    import secrets

    return secrets.token_urlsafe(32), secrets.token_urlsafe(32)


def upsert_subscription(
    session,
    email: str,
    category: str,
    auto_confirm: bool,
):
    from sqlmodel import select

    from app.models import Subscription

    existing = session.exec(
        select(Subscription).where(Subscription.email == email, Subscription.category == category)
    ).first()

    if existing:
        if auto_confirm:
            existing.active = True
            existing.confirmed = True
        session.add(existing)
        session.commit()
        return existing

    confirm_token, unsub_token = new_tokens()
    sub = Subscription(
        email=email,
        category=category,
        active=auto_confirm,
        confirmed=auto_confirm,
        confirm_token=confirm_token,
        unsub_token=unsub_token,
    )
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub
