from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.config import settings
from app.db import engine
from app.models import DigestLog, Subscription
from app.services.emailer import send_email
from app.services.cache import persist_articles, purge_old_content
from app.services.news import CATEGORY_QUERIES, get_news, fetch_news
from app.services.observability import log_event


def send_digest_for_subscription(subscription_id: int) -> None:
    with Session(engine) as session:
        purge_old_content(session)
        sub = session.exec(select(Subscription).where(Subscription.id == subscription_id)).first()
        if not sub or not sub.active or not sub.confirmed:
            return

        items, _, from_db = get_news(session, category=sub.category, page=1, page_size=5)
        if not from_db:
            persist_articles(session, items)
        if not items:
            return
        top_items = items[:5]
        html_items = "".join(
            f"<li><a href='{item.url}'>{item.title}</a> - {item.source}</li>"
            for item in top_items
        )
        unsubscribe_link = f"{settings.public_base_url}/unsubscribe?token={sub.unsub_token}"
        html = (
            f"<h2>Tu resumen diario de IA ({sub.category})</h2>"
            f"<ul>{html_items}</ul>"
            f"<p>Siempre verifica la fuente original.</p>"
            f"<p><a href='{unsubscribe_link}'>Cancelar suscripción</a></p>"
        )

        send_email(
            subject=f"Noticias IA · {sub.category}",
            html=html,
            recipient=sub.email,
        )

        session.add(DigestLog(subscription_id=sub.id, sent_at=datetime.utcnow()))
        sub.last_sent_at = datetime.utcnow()
        session.add(sub)
        session.commit()
        log_event("digest_sent", subscription_id=sub.id, email=sub.email)


def refresh_news_cache() -> None:
    with Session(engine) as session:
        purge_old_content(session)
        for category in CATEGORY_QUERIES.keys():
            items, _ = fetch_news(category=category, page=1, page_size=settings.news_prefetch_page_size)
            if items:
                persist_articles(session, items)


def send_single_email(email: str, subject: str, html: str) -> None:
    send_email(subject=subject, html=html, recipient=email)
