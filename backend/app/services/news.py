from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.schemas import Article

CATEGORY_QUERIES = {
    "research": "AI research OR machine learning paper",
    "industry": "AI industry OR startup OR product launch",
    "policy": "AI regulation OR policy OR government",
    "security": "AI security OR safety OR risk",
    "tools": "AI tools OR models OR platforms",
}

SAMPLE_NEWS = [
    Article(
        title="AI policy roadmap highlights safety priorities",
        description="Policy groups release a new framework for responsible AI adoption.",
        url="https://www.bbc.com/news/technology",
        source="BBC News",
        published_at=datetime.utcnow(),
        image_url=None,
        category="policy",
    ),
    Article(
        title="New open research model sets efficiency records",
        description="Researchers introduce a lightweight model with strong benchmarks.",
        url="https://www.technologyreview.com/",
        source="MIT Technology Review",
        published_at=datetime.utcnow(),
        image_url=None,
        category="research",
    ),
]


def _allowed_sources() -> list[str]:
    return [source.strip() for source in settings.news_allowed_sources.split(",") if source.strip()]


def _build_query(category: str | None, q: str | None) -> str:
    base = q or "artificial intelligence OR machine learning"
    if category and category in CATEGORY_QUERIES:
        return f"({base}) AND ({CATEGORY_QUERIES[category]})"
    return base


def fetch_news(category: str | None = None, q: str | None = None) -> list[Article]:
    if not settings.news_api_key:
        return [item for item in SAMPLE_NEWS if not category or item.category == category]

    params: dict[str, Any] = {
        "apiKey": settings.news_api_key,
        "q": _build_query(category, q),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "from": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
    }

    allowed_sources = _allowed_sources()
    if allowed_sources:
        params["sources"] = ",".join(allowed_sources)

    with httpx.Client(timeout=15) as client:
        response = client.get(f"{settings.news_api_base}/everything", params=params)
        response.raise_for_status()
        data = response.json()

    items: list[Article] = []
    for article in data.get("articles", []):
        source_name = article.get("source", {}).get("name") or ""
        item = Article(
            title=article.get("title") or "(Sin titulo)",
            description=article.get("description"),
            url=article.get("url"),
            source=source_name,
            published_at=_safe_date(article.get("publishedAt")),
            image_url=article.get("urlToImage"),
            category=category,
        )
        items.append(item)

    return items


def _safe_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
