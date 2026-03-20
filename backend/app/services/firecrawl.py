from __future__ import annotations

import httpx

from app.config import settings


def scrape_markdown(url: str) -> str | None:
    if not settings.firecrawl_api_key:
        return None

    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "blockAds": True,
        "storeInCache": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=25) as client:
        response = client.post(f"{settings.firecrawl_base}/scrape", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    content = data.get("data", {}).get("markdown")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None
