from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Iterable

from sqlmodel import Session, select

from app.config import settings
from app.models import ArticleRecord, NewsCache
from app.schemas import Article


def cache_key(parts: Iterable[str]) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_cache(session: Session, key: str) -> list[Article] | None:
    item = session.exec(select(NewsCache).where(NewsCache.cache_key == key)).first()
    if not item:
        return None

    age = datetime.utcnow() - item.created_at
    if age > timedelta(minutes=settings.news_cache_ttl_minutes):
        session.delete(item)
        session.commit()
        return None

    try:
        payload = json.loads(item.payload)
        return [Article(**entry) for entry in payload]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def save_cache(session: Session, key: str, articles: list[Article]) -> None:
    payload = json.dumps([article.model_dump() for article in articles])
    existing = session.exec(select(NewsCache).where(NewsCache.cache_key == key)).first()
    if existing:
        existing.payload = payload
        existing.created_at = datetime.utcnow()
        session.add(existing)
    else:
        session.add(NewsCache(cache_key=key, payload=payload))
    session.commit()


def persist_articles(session: Session, articles: list[Article]) -> None:
    for article in articles:
        if not article.url:
            continue
        existing = session.exec(select(ArticleRecord).where(ArticleRecord.url == article.url)).first()
        if existing:
            existing.title = article.title
            existing.description = article.description
            existing.source_domain = article.source_domain or article.source
            existing.published_at = article.published_at
            existing.image_url = article.image_url
            existing.category = article.category
            existing.trust_score = article.trust_score or existing.trust_score
            existing.fetched_at = datetime.utcnow()
            session.add(existing)
        else:
            session.add(
                ArticleRecord(
                    url=article.url,
                    title=article.title,
                    description=article.description,
                    source_domain=article.source_domain or article.source,
                    published_at=article.published_at,
                    image_url=article.image_url,
                    category=article.category,
                    trust_score=article.trust_score or 1.0,
                )
            )
    session.commit()
