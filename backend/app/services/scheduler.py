from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.config import settings
from app.db import engine
from app.models import Subscription
from app.services.emailer import send_email
from app.services.news import fetch_news


_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=settings.timezone)
    return _scheduler


def start_scheduler() -> None:
    scheduler = get_scheduler()
    trigger = CronTrigger(hour=settings.daily_digest_hour, minute=0)
    scheduler.add_job(send_daily_digest, trigger, id="daily_digest", replace_existing=True)
    scheduler.start()


def send_daily_digest() -> None:
    with Session(engine) as session:
        subs = session.exec(select(Subscription).where(Subscription.active == True)).all()

    for sub in subs:
        items = fetch_news(category=sub.category)
        if not items:
            continue
        top_items = items[:5]
        html_items = "".join(
            f"<li><a href='{item.url}'>{item.title}</a> - {item.source}</li>"
            for item in top_items
        )
        html = (
            f"<h2>Tu resumen diario de IA ({sub.category})</h2>"
            f"<ul>{html_items}</ul>"
            f"<p>Siempre verifica la fuente original.</p>"
        )
        try:
            send_email(
                subject=f"Noticias IA · {sub.category}",
                html=html,
                recipient=sub.email,
            )
        except RuntimeError:
            continue
