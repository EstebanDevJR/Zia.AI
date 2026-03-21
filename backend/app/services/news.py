from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlmodel import Session, select

from app.config import settings
from app.models import ArticleRecord
from app.schemas import Article
from app.services.categories import CATEGORY_HINTS, CATEGORY_QUERIES
from app.services.classifier import classify_article
from app.services.ddg import search_ddg
from app.services.observability import EXTERNAL_CALLS, log_event
from app.services.validator import validate_article

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "llm",
    "large language model",
    "generative",
    "gen ai",
    "deep learning",
    "chatgpt",
    "openai",
    "anthropic",
    "claude",
    "gpt",
    "gemini",
    "copilot",
    "deepmind",
    "mistral",
    "llama",
    "nvidia ai",
]

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


def _is_ai_related(text: str | None) -> bool:
    if not text:
        return False
    haystack = text.lower()
    return any(keyword in haystack for keyword in AI_KEYWORDS)


def _matches_category(text: str | None, category: str | None) -> bool:
    if not text or not category:
        return True
    hints = CATEGORY_HINTS.get(category)
    if not hints:
        return True
    haystack = text.lower()
    return any(hint in haystack for hint in hints)


def _is_listing_url(url: str) -> bool:
    try:
        path = urlparse(url).path.lower()
    except ValueError:
        return True
    segments = [segment for segment in path.split("/") if segment]
    if len(segments) <= 1:
        return True
    listing_markers = (
        "/topic/",
        "/topics/",
        "/category/",
        "/categories/",
        "/tag/",
        "/tags/",
        "/section/",
        "/sections/",
        "/author/",
        "/authors/",
    )
    return any(marker in path for marker in listing_markers)


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
    validated_items, has_more = _validate_and_slice(items, validation_query, page, page_size, category)
    return validated_items, has_more


def get_news(
    session: Session,
    category: str | None = None,
    q: str | None = None,
    lang: str | None = None,
    page: int = 1,
    page_size: int = 8,
    fast: bool = False,
) -> tuple[list[Article], bool, bool]:
    items, has_more = _fetch_from_db(session, category, q, page, page_size)
    if items and (len(items) >= page_size or has_more):
        return items, has_more, True

    if fast:
        limit = _limit_for_page(page, page_size)
        if category and settings.classification_force_llm_for_filters:
            limit = min(limit, settings.classification_max_candidates)
        raw_items = _fetch_raw(category=category, q=q, lang=lang, limit=limit)
        start = (page - 1) * page_size
        end = start + page_size
        return raw_items[start:end], len(raw_items) > end, False

    items, has_more = fetch_news(category=category, q=q, lang=lang, page=page, page_size=page_size)
    return items, has_more, False


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
        if _is_listing_url(url):
            continue
        if allowed_domains and not _is_allowed(url, allowed_domains):
            continue

        title = result.get("title") or "(Sin titulo)"
        description = result.get("description") or result.get("snippet")
        combined = f"{title} {description or ''}"
        if not _is_ai_related(combined):
            continue
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

    return _classify_and_filter(items, category)


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
        if _is_listing_url(url):
            continue
        if allowed_domains and not _is_allowed(url, allowed_domains):
            continue

        domain = _domain_from_url(url)
        title = result.get("title") or "(Sin titulo)"
        description = result.get("snippet")
        combined = f"{title} {description or ''}"
        if not _is_ai_related(combined):
            continue
        items.append(
            Article(
                title=title,
                description=description,
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

    return _classify_and_filter(items, category)


def _validate_and_slice(
    items: list[Article],
    query: str | None,
    page: int,
    page_size: int,
    category: str | None,
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
        try:
            is_valid, context = validate_article(item, query)
        except Exception:
            is_valid, context = False, None
        if is_valid:
            combined = f"{item.title} {item.description or ''} {context or ''}"
            if not _is_ai_related(combined):
                continue
            if context and not _is_ai_related(context):
                continue
            predicted, _ = classify_article(
                item,
                context=context,
                force_llm=bool(category and settings.classification_force_llm_for_filters),
                target_category=category,
            )
            if predicted:
                item.category = predicted
            if category and predicted != category:
                continue
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


def _fetch_from_db(
    session: Session,
    category: str | None,
    q: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Article], bool]:
    cutoff = datetime.utcnow() - timedelta(hours=settings.article_ttl_hours)
    stmt = select(ArticleRecord).where(ArticleRecord.fetched_at >= cutoff)
    if category:
        stmt = stmt.where(ArticleRecord.category == category)
    records = session.exec(stmt).all()

    items: list[tuple[Article, datetime]] = []
    query_tokens = _query_tokens(q)

    for record in records:
        combined = f"{record.title} {record.description or ''} {record.context or ''}".lower()
        if query_tokens and not any(token in combined for token in query_tokens):
            continue
        items.append(
            (
                Article(
                    title=record.title,
                    description=record.description,
                    url=record.url,
                    source=record.source_domain,
                    published_at=record.published_at,
                    image_url=record.image_url,
                    category=record.category,
                    source_domain=record.source_domain,
                    trust_score=record.trust_score,
                    context=record.context,
                ),
                record.fetched_at,
            )
        )

    items.sort(key=lambda pair: pair[0].published_at or pair[1], reverse=True)
    articles = [pair[0] for pair in items]
    start = (page - 1) * page_size
    end = start + page_size
    return articles[start:end], len(articles) > end


def _query_tokens(q: str | None) -> list[str]:
    if not q:
        return []
    tokens = [token.strip().lower() for token in q.split() if len(token.strip()) >= 3]
    return tokens[:6]


def _classify_and_filter(items: list[Article], category: str | None) -> list[Article]:
    if not settings.classification_enabled and not category:
        return items
    filtered: list[Article] = []
    for item in items:
        predicted, _ = classify_article(
            item,
            force_llm=bool(category and settings.classification_force_llm_for_filters),
            target_category=category,
        )
        if predicted:
            item.category = predicted
        if category and predicted != category:
            continue
        filtered.append(item)
    return filtered


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
