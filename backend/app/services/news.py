from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.schemas import Article

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
    ),
    Article(
        title="New open research model sets efficiency records",
        description="Researchers introduce a lightweight model with strong benchmarks.",
        url="https://www.technologyreview.com/",
        source="technologyreview.com",
        published_at=datetime.utcnow(),
        image_url=None,
        category="research",
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


def fetch_news(category: str | None = None, q: str | None = None) -> list[Article]:
    if not settings.firecrawl_api_key:
        return [item for item in SAMPLE_NEWS if not category or item.category == category]

    allowed_domains = _allowed_domains()
    query = _build_query(category, q)
    query = _with_domain_filter(query, allowed_domains)

    payload: dict[str, Any] = {
        "query": query,
        "limit": 20,
        "sources": ["news"],
    }

    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=20) as client:
        response = client.post(f"{settings.firecrawl_base}/search", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    results = _extract_results(data)
    items: list[Article] = []

    for result in results:
        url = result.get("url")
        if not url:
            continue
        if allowed_domains and not _is_allowed(url, allowed_domains):
            continue

        title = result.get("title") or "(Sin titulo)"
        description = result.get("description") or result.get("snippet")
        date_value = result.get("date") or result.get("publishedDate") or result.get("published_at")
        image_url = result.get("imageUrl") or result.get("image")

        item = Article(
            title=title,
            description=description,
            url=url,
            source=_domain_from_url(url),
            published_at=_safe_date(date_value),
            image_url=image_url,
            category=category,
        )
        items.append(item)

    return items


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
