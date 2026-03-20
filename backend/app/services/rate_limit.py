from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import RateLimitEvent


def check_rate_limit(
    session: Session,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    event = session.exec(
        select(RateLimitEvent).where(
            RateLimitEvent.key == key,
            RateLimitEvent.window_start >= window_start,
        )
    ).first()

    if not event:
        event = RateLimitEvent(key=key, window_start=now, count=1)
        session.add(event)
        session.commit()
        return

    if event.count >= limit:
        raise HTTPException(status_code=429, detail="Rate limit excedido")

    event.count += 1
    session.add(event)
    session.commit()
