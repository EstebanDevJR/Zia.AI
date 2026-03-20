from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.config import settings


class _DDGParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, Any]] = []
        self._current: dict[str, str] = {}
        self._in_title = False
        self._in_snippet = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        class_name = attr_map.get("class", "")

        if tag == "a" and "result__a" in class_name:
            self._flush_current()
            href = attr_map.get("href", "")
            self._current = {"url": _clean_url(href), "title": "", "snippet": ""}
            self._in_title = True
            return

        if "result__snippet" in class_name:
            self._in_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title:
            self._in_title = False
        if self._in_snippet and tag in {"a", "div", "span"}:
            self._in_snippet = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._current["title"] = (self._current.get("title", "") + data).strip()
        elif self._in_snippet:
            self._current["snippet"] = (self._current.get("snippet", "") + data).strip()

    def close(self) -> None:
        self._flush_current()
        super().close()

    def _flush_current(self) -> None:
        if self._current.get("url") and self._current.get("title"):
            self.results.append(self._current)
        self._current = {}


def _clean_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        query = parse_qs(parsed.query)
        uddg = query.get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return url


def search_ddg(query: str, limit: int = 20, accept_language: str | None = None) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": settings.ddg_user_agent,
        "Accept-Language": accept_language or settings.ddg_accept_language,
        "Referer": "https://html.duckduckgo.com/",
    }
    data = {
        "q": query,
    }

    with httpx.Client(timeout=20) as client:
        response = client.post(settings.ddg_base, data=data, headers=headers)
        response.raise_for_status()
        html = response.text

    parser = _DDGParser()
    parser.feed(html)
    parser.close()

    return parser.results[:limit]
