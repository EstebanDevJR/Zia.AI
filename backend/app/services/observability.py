from __future__ import annotations

import json
import logging
import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, make_asgi_app

logger = logging.getLogger("zia")

REQUEST_COUNT = Counter(
    "zia_requests_total",
    "Total requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "zia_request_latency_seconds",
    "Request latency",
    ["method", "path"],
)
EXTERNAL_CALLS = Counter(
    "zia_external_calls_total",
    "External calls",
    ["service", "status"],
)


def init_logging() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_event(event: str, **fields: object) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))


def metrics_app():
    return make_asgi_app()


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start

    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)

    return response
