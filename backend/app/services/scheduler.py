from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.config import settings
from app.db import engine
from app.models import Subscription
from app.services.queue import enqueue_job
from app.services.tasks import send_digest_for_subscription


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
        subs = session.exec(
            select(Subscription).where(Subscription.active == True, Subscription.confirmed == True)
        ).all()

    for sub in subs:
        job = enqueue_job("app.services.tasks.send_digest_for_subscription", sub.id)
        if job is None:
            send_digest_for_subscription(sub.id)
