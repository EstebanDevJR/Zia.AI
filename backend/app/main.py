from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
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
from app.services.cache import cache_key, load_cache, persist_articles, purge_old_content, save_cache
from app.services.emailer import send_email, smtp_configured
from app.services.firecrawl import scrape_markdown
from app.services.categories import CATEGORY_QUERIES
from app.services.news import get_news, upsert_subscription
from app.services.observability import init_logging, log_event, metrics_app, metrics_middleware
from app.services.queue import enqueue_job
from app.services.rate_limit import check_rate_limit
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
app.middleware("http")(metrics_middleware)

app.mount("/metrics", metrics_app())


@app.on_event("startup")
def on_startup() -> None:
    init_logging()
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
def news(
    request: Request,
    category: str | None = None,
    q: str | None = None,
    lang: str | None = None,
    page: int = 1,
    page_size: int | None = None,
    fast: bool = False,
) -> NewsResponse:
    if category == "all":
        category = None
    if page < 1:
        page = 1
    if page_size is None:
        page_size = settings.news_page_size_default
    if page_size < 1:
        page_size = settings.news_page_size_default
    page_size = min(page_size, settings.news_page_size_max)

    cache_id = cache_key([category or "all", q or "", lang or "", str(page), str(page_size), str(fast)])
    with next(get_session()) as session:
        purge_old_content(session)
        cached = load_cache(session, cache_id)
        if cached:
            items, has_more = cached
            return NewsResponse(items=items, page=page, page_size=page_size, has_more=has_more)

        items, has_more, from_db = get_news(
            session,
            category=category,
            q=q,
            lang=lang,
            page=page,
            page_size=page_size,
            fast=fast,
        )
        if not from_db:
            persist_articles(session, items)
        save_cache(session, cache_id, items, has_more=has_more)

    log_event("news_fetch", ip=request.client.host if request.client else "unknown")
    return NewsResponse(items=items, page=page, page_size=page_size, has_more=has_more)


@app.post("/summary", response_model=SummaryResponse)
def summary(
    request: Request,
    payload: SummaryRequest,
    session: Session = Depends(get_session),
) -> SummaryResponse:
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(
        session,
        key=f"summary:{client_ip}",
        limit=settings.rate_limit_summary_per_hour,
        window_seconds=3600,
    )

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
def send(payload: SendRequest, request: Request, session: Session = Depends(get_session)) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(
        session,
        key=f"send:{client_ip}",
        limit=settings.rate_limit_send_per_hour,
        window_seconds=3600,
    )
    check_rate_limit(
        session,
        key=f"send:{payload.email}",
        limit=settings.rate_limit_send_per_hour,
        window_seconds=3600,
    )

    article = payload.article
    html = (
        f"<h2>{article.title}</h2>"
        f"<p>{article.description or ''}</p>"
        f"<p>Fuente: {article.source}</p>"
        f"<p><a href='{article.url}'>Ver noticia original</a></p>"
    )

    if not smtp_configured():
        raise HTTPException(status_code=400, detail="SMTP no configurado")

    job = enqueue_job("app.services.tasks.send_single_email", payload.email, "Noticia IA", html)
    if job is None:
        try:
            send_email(subject="Noticia IA", html=html, recipient=payload.email)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "queued" if job else "sent"}


@app.post("/subscribe", response_model=SubscriptionResponse)
def subscribe(
    payload: SubscribeRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> SubscriptionResponse:
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(
        session,
        key=f"subscribe:{client_ip}",
        limit=settings.rate_limit_subscribe_per_hour,
        window_seconds=3600,
    )
    check_rate_limit(
        session,
        key=f"subscribe:{payload.email}",
        limit=settings.rate_limit_subscribe_per_hour,
        window_seconds=3600,
    )

    auto_confirm = not smtp_configured()
    sub = upsert_subscription(session, payload.email, payload.category, auto_confirm=auto_confirm)

    if not auto_confirm:
        confirm_link = f"{settings.public_base_url}/confirm?token={sub.confirm_token}"
        html = (
            f"<p>Confirma tu suscripción a noticias de IA ({sub.category}).</p>"
            f"<p><a href='{confirm_link}'>Confirmar suscripción</a></p>"
        )
        job = enqueue_job("app.services.tasks.send_single_email", sub.email, "Confirma tu suscripción", html)
        if job is None:
            send_email(subject="Confirma tu suscripción", html=html, recipient=sub.email)

    return SubscriptionResponse(
        id=sub.id,
        email=sub.email,
        category=sub.category,
        active=sub.active,
        confirmed=sub.confirmed,
    )


@app.get("/confirm")
def confirm(token: str, session: Session = Depends(get_session)) -> dict:
    sub = session.exec(select(Subscription).where(Subscription.confirm_token == token)).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Token inválido")
    sub.active = True
    sub.confirmed = True
    session.add(sub)
    session.commit()
    return {"status": "confirmed"}


@app.get("/unsubscribe")
def unsubscribe(token: str, session: Session = Depends(get_session)) -> dict:
    sub = session.exec(select(Subscription).where(Subscription.unsub_token == token)).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Token inválido")
    sub.active = False
    session.add(sub)
    session.commit()
    return {"status": "unsubscribed"}
