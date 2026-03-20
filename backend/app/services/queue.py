from __future__ import annotations

from rq import Queue
from rq.job import Job

from app.config import settings

try:
    from redis import Redis
except ImportError:  # pragma: no cover
    Redis = None  # type: ignore


def get_queue() -> Queue | None:
    if Redis is None:
        return None
    try:
        connection = Redis.from_url(settings.redis_url)
        return Queue("default", connection=connection)
    except Exception:
        return None


def enqueue_job(func_path: str, *args, **kwargs) -> Job | None:
    queue = get_queue()
    if not queue:
        return None
    return queue.enqueue(func_path, *args, **kwargs)
