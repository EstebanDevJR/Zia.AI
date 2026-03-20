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

    cleaned = _clean_boilerplate(text)
    excerpt = _pick_sentences(cleaned)

    return title, excerpt, response.status_code, content_type


def _clean_boilerplate(text: str) -> str:
    patterns = [
        r"skip to (main )?content",
        r"skip to navigation",
        r"sign in",
        r"subscribe",
        r"advertisement",
        r"cookie(s)?",
        r"privacy policy",
        r"terms of service",
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _pick_sentences(text: str, max_chars: int = 1200) -> str | None:
    if not text:
        return None
    sentences = re.split(r"(?<=[.!?])\s+", text)
    picked: list[str] = []
    total = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 40:
            continue
        picked.append(sentence)
        total += len(sentence) + 1
        if total >= max_chars or len(picked) >= 3:
            break
    if picked:
        return " ".join(picked)
    return text[:max_chars].strip()
