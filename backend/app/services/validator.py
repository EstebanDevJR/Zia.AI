from __future__ import annotations

from app.agent.validate import build_graph
from app.schemas import Article


_graph = None


def validate_article(article: Article, query: str | None = None) -> tuple[bool, str | None]:
    global _graph
    if _graph is None:
        _graph = build_graph()
    graph = _graph
    result = graph.invoke(
        {
            "url": article.url,
            "title": article.title,
            "description": article.description,
            "query": query,
            "fetched_title": None,
            "fetched_text": None,
            "ok": False,
            "valid": False,
            "context": None,
        }
    )
    return bool(result.get("valid")), result.get("context")
