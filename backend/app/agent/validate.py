from __future__ import annotations

import json
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.content_fetcher import fetch_html_context
from app.services.firecrawl import scrape_page


class ValidateState(TypedDict):
    url: str
    title: str
    description: str | None
    query: str | None
    fetched_title: str | None
    fetched_text: str | None
    ok: bool
    valid: bool
    context: str | None


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0.1)


def build_graph():
    graph = StateGraph(ValidateState)

    def fetch(state: ValidateState) -> ValidateState:
        fetched_title = None
        fetched_text = None
        ok = False

        data = scrape_page(state["url"])
        if data:
            fetched_title = data.get("metadata", {}).get("title") or data.get("title")
            markdown = data.get("markdown")
            if isinstance(markdown, str):
                fetched_text = _compact(markdown)
            status = data.get("metadata", {}).get("statusCode")
            ok = bool(markdown) and (status is None or status < 400)
        else:
            title, text, status, content_type = fetch_html_context(state["url"])
            fetched_title = title
            fetched_text = text
            ok = bool(text) and (status is None or status < 400) and (content_type is None or "text/html" in content_type)

        return {
            **state,
            "fetched_title": fetched_title,
            "fetched_text": fetched_text,
            "ok": ok,
        }

    def validate(state: ValidateState) -> ValidateState:
        if not state.get("ok"):
            return {**state, "valid": False, "context": None}

        if settings.validation_use_llm and settings.openai_api_key:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Evalua si la pagina corresponde a la noticia. "
                        "Responde solo JSON: {\\"valid\\": true/false, \\"context\\": \\"...\\"}. "
                        "El contexto debe ser 2-3 frases sin inventar datos."
                    ),
                    (
                        "human",
                        "Query: {query}\nTitulo noticia: {title}\nDescripcion: {description}\nTitulo pagina: {page_title}\nTexto pagina: {page_text}",
                    ),
                ]
            )
            chain = prompt | _llm() | StrOutputParser()
            raw = chain.invoke(
                {
                    "title": state["title"],
                    "description": state.get("description") or "",
                    "query": state.get("query") or "",
                    "page_title": state.get("fetched_title") or "",
                    "page_text": _safe_slice(state.get("fetched_text")),
                }
            )
            parsed = _parse_json(raw)
            if parsed:
                return {
                    **state,
                    "valid": bool(parsed.get("valid")),
                    "context": _trim_context(parsed.get("context")),
                }

        valid = _heuristic_match(
            state["title"],
            state.get("description"),
            state.get("fetched_title"),
            state.get("fetched_text"),
        )
        context = _trim_context(state.get("fetched_text")) if valid else None
        return {**state, "valid": valid, "context": context}

    graph.add_node("fetch", fetch)
    graph.add_node("validate", validate)
    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


def _compact(text: str) -> str:
    clean = re.sub(r"\s+", " ", text)
    return clean.strip()


def _safe_slice(text: str | None) -> str:
    if not text:
        return ""
    return text[:2000]


def _trim_context(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = _compact(text)
    return cleaned[: settings.context_max_chars].rsplit(" ", 1)[0] if len(cleaned) > settings.context_max_chars else cleaned


def _parse_json(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return None


def _heuristic_match(
    title: str,
    description: str | None,
    fetched_title: str | None,
    fetched_text: str | None,
) -> bool:
    tokens = _tokens(f"{title} {description or ''}")
    if not tokens:
        return True

    haystack = _tokens(f"{fetched_title or ''} {fetched_text or ''}")
    if not haystack:
        return False

    overlap = len(tokens.intersection(haystack))
    return overlap >= max(2, int(len(tokens) * 0.2))


def _tokens(text: str) -> set[str]:
    stop = {
        "the", "and", "of", "for", "with", "a", "an", "in", "on", "to", "la", "el", "de", "y", "en", "con"
    }
    words = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}", text.lower())
    return {word for word in words if word not in stop}
