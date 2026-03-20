from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

import httpx


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._in_title:
            self.title += data


def fetch_html_context(url: str, timeout: int = 12) -> tuple[str | None, str | None, int | None, str | None]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            status = response.status_code
            content_type = response.headers.get("content-type", "")
            if status >= 400 or "text/html" not in content_type:
                return None, None, status, content_type

            html = response.text
    except httpx.HTTPError:
        return None, None, None, None

    title_parser = _TitleParser()
    try:
        title_parser.feed(html)
    except Exception:
        pass

    title = unescape(title_parser.title.strip()) if title_parser.title else None

    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    excerpt = text[:1200] if text else None

    return title, excerpt, response.status_code, content_type
