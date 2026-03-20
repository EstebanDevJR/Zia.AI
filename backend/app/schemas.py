from datetime import datetime
from pydantic import BaseModel, EmailStr


class Article(BaseModel):
    title: str
    description: str | None = None
    url: str
    source: str
    published_at: datetime | None = None
    image_url: str | None = None
    category: str | None = None
    source_domain: str | None = None
    trust_score: float | None = None
    context: str | None = None


class NewsResponse(BaseModel):
    items: list[Article]
    page: int
    page_size: int
    has_more: bool


class SummaryRequest(BaseModel):
    article: Article


class SummaryResponse(BaseModel):
    summary: str


class SendRequest(BaseModel):
    email: EmailStr
    article: Article


class SubscribeRequest(BaseModel):
    email: EmailStr
    category: str


class SubscriptionResponse(BaseModel):
    id: int
    email: EmailStr
    category: str
    active: bool
    confirmed: bool
