from __future__ import annotations

import httpx

from app.config import settings


def scrape_markdown(url: str) -> str | None:
    data = scrape_page(url)
    content = data.get("markdown") if data else None
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def scrape_page(url: str) -> dict | None:
    if not settings.firecrawl_api_key:
        return None

    payload = {
        "url": url,
        "formats": [{"type": "markdown"}],
        "onlyMainContent": True,
        "blockAds": True,
        "storeInCache": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=25) as client:
            response = client.post(f"{settings.firecrawl_base}/scrape", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data.get("data") or {}
    except httpx.HTTPError:
        return None
