from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session, init_db
from app.models import SummaryCache, Subscription
from app.schemas import (
    NewsResponse,
    SendRequest,
    SubscribeRequest,
    SubscriptionResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.emailer import send_email
from app.services.firecrawl import scrape_markdown
from app.services.news import CATEGORY_QUERIES, fetch_news
from app.services.scheduler import start_scheduler
from app.services.summarize import summarize_text

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    if settings.enable_scheduler:
        start_scheduler()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/categories")
def categories() -> list[str]:
    return list(CATEGORY_QUERIES.keys())


@app.get("/news", response_model=NewsResponse)
def news(category: str | None = None, q: str | None = None) -> NewsResponse:
    items = fetch_news(category=category, q=q)
    return NewsResponse(items=items)


@app.post("/summary", response_model=SummaryResponse)
def summary(payload: SummaryRequest, session: Session = Depends(get_session)) -> SummaryResponse:
    cached = session.exec(select(SummaryCache).where(SummaryCache.url == payload.article.url)).first()
    if cached:
        return SummaryResponse(summary=cached.summary)

    scraped = scrape_markdown(payload.article.url)
    if scraped:
        trimmed = scraped[:6000]
        text = (
            f"{payload.article.title}\n"
            f"{payload.article.description or ''}\n\n"
            f"Contenido:\n{trimmed}"
        )
    else:
        text = f"{payload.article.title}\n{payload.article.description or ''}\nFuente: {payload.article.source}"
    summary_text = summarize_text(text)

    cache = SummaryCache(url=payload.article.url, summary=summary_text)
    session.add(cache)
    session.commit()

    return SummaryResponse(summary=summary_text)


@app.post("/send")
def send(payload: SendRequest) -> dict:
    article = payload.article
    html = (
        f"<h2>{article.title}</h2>"
        f"<p>{article.description or ''}</p>"
        f"<p>Fuente: {article.source}</p>"
        f"<p><a href='{article.url}'>Ver noticia original</a></p>"
    )
    try:
        send_email(subject="Noticia IA", html=html, recipient=payload.email)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "sent"}


@app.post("/subscribe", response_model=SubscriptionResponse)
def subscribe(payload: SubscribeRequest, session: Session = Depends(get_session)) -> SubscriptionResponse:
    existing = session.exec(
        select(Subscription).where(
            Subscription.email == payload.email,
            Subscription.category == payload.category,
        )
    ).first()

    if existing:
        if not existing.active:
            existing.active = True
            session.add(existing)
            session.commit()
        return SubscriptionResponse(
            id=existing.id,
            email=existing.email,
            category=existing.category,
            active=existing.active,
        )

    sub = Subscription(email=payload.email, category=payload.category)
    session.add(sub)
    session.commit()
    session.refresh(sub)

    return SubscriptionResponse(
        id=sub.id,
        email=sub.email,
        category=sub.category,
        active=sub.active,
    )
