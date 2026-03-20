from __future__ import annotations

from rq import Worker
from redis import Redis

from app.config import settings


def main() -> None:
    connection = Redis.from_url(settings.redis_url)
    worker = Worker(["default"], connection=connection)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
