from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.agent.classify import build_graph, _llm
from app.config import settings
from app.schemas import Article
from app.services.categories import CATEGORY_HINTS

CATEGORY_DEFS = {
    "research": "academic research, papers, arXiv, benchmarks, datasets, model training",
    "industry": "companies, products, funding, acquisitions, partnerships, commercial launches",
    "policy": "government policy, regulation, legislation, compliance, public-sector decisions",
    "security": "AI safety, risk, security, misuse, red-teaming, cyber incidents",
    "tools": "developer tools, APIs, platforms, assistants, SDKs, workflows, features",
}

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def classify_article(
    article: Article,
    context: str | None = None,
    force_llm: bool = False,
    target_category: str | None = None,
) -> tuple[str | None, float]:
    if not settings.classification_enabled:
        return article.category, 1.0

    state = {
        "title": article.title,
        "description": article.description,
        "context": context,
        "category": None,
        "confidence": 0.0,
    }

    if target_category and force_llm and settings.openai_api_key:
        match, confidence = _llm_match_category(target_category, state)
        if match and confidence >= settings.classification_min_confidence:
            return target_category, confidence
        return None, confidence

    heuristic_category, heuristic_confidence = _heuristic_classify(article, context)
    if not force_llm and not settings.classification_use_llm:
        return heuristic_category, heuristic_confidence

    if settings.openai_api_key:
        graph = _get_graph()
        result = graph.invoke(state)
        category = _normalize_category(result.get("category"))
        confidence = float(result.get("confidence") or 0.0)
        if category and confidence >= settings.classification_min_confidence:
            return category, confidence

    return heuristic_category, heuristic_confidence


def _heuristic_classify(article: Article, context: str | None) -> tuple[str | None, float]:
    text = f"{article.title} {article.description or ''} {context or ''}".lower()
    scores: dict[str, int] = {key: 0 for key in CATEGORY_HINTS}
    for category, hints in CATEGORY_HINTS.items():
        for hint in hints:
            if hint in text:
                scores[category] += 1

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    if best_score <= 1:
        return None, 0.0
    confidence = min(0.9, best_score / 3)
    if confidence < settings.classification_min_confidence:
        return None, confidence
    return best_category, confidence


def _normalize_category(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    if value in CATEGORY_HINTS:
        return value
    return None


def _llm_match_category(category: str, state: dict) -> tuple[bool, float]:
    definition = CATEGORY_DEFS.get(category, category)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Responde si la noticia corresponde a la categoria dada. "
                "Responde solo JSON: {{\"match\": true/false, \"confidence\": 0.0-1.0}}.",
            ),
            (
                "human",
                "Categoria: {category} ({definition})\nTitulo: {title}\nDescripcion: {description}\nContexto: {context}",
            ),
        ]
    )
    chain = prompt | _llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "category": category,
            "definition": definition,
            "title": state["title"],
            "description": state.get("description") or "",
            "context": state.get("context") or "",
        }
    )
    parsed = _parse_json(raw)
    if parsed:
        match = bool(parsed.get("match"))
        confidence = parsed.get("confidence")
        if isinstance(confidence, (float, int)):
            return match, float(confidence)
    return False, 0.0


def _parse_json(raw: str) -> dict | None:
    import json

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return None
