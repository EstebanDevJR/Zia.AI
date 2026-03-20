from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    category: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=False)
    confirmed: bool = Field(default=False)
    confirm_token: str = Field(index=True)
    unsub_token: str = Field(index=True)
    last_sent_at: datetime | None = None


class SummaryCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(sa_column=Column(String, unique=True, index=True))
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArticleRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(sa_column=Column(String, unique=True, index=True))
    title: str
    description: str | None = None
    source_domain: str
    published_at: datetime | None = None
    image_url: str | None = None
    category: str | None = Field(default=None, index=True)
    trust_score: float = Field(default=1.0)
    fetched_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class NewsCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cache_key: str = Field(index=True, unique=True)
    payload: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class RateLimitEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True)
    window_start: datetime = Field(index=True)
    count: int = Field(default=0)


class DigestLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(index=True)
    sent_at: datetime = Field(default_factory=datetime.utcnow, index=True)
