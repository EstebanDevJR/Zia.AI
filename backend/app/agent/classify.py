from __future__ import annotations

import json
from typing import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings


class ClassifyState(TypedDict):
    title: str
    description: str | None
    context: str | None
    category: str | None
    confidence: float


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0.1)


def build_graph():
    graph = StateGraph(ClassifyState)

    def classify(state: ClassifyState) -> ClassifyState:
        if not settings.classification_use_llm or not settings.openai_api_key:
            return state

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Clasifica la noticia en una de estas categorias: research, industry, policy, security, tools, unknown. "
                    "Responde solo JSON: {{\"category\": \"...\", \"confidence\": 0.0-1.0}}.",
                ),
                (
                    "human",
                    "Titulo: {title}\nDescripcion: {description}\nContexto: {context}",
                ),
            ]
        )
        chain = prompt | _llm() | StrOutputParser()
        raw = chain.invoke(
            {
                "title": state["title"],
                "description": state.get("description") or "",
                "context": _safe_slice(state.get("context")),
            }
        )
        parsed = _parse_json(raw)
        if parsed:
            category = parsed.get("category")
            confidence = parsed.get("confidence")
            return {
                **state,
                "category": str(category) if category else None,
                "confidence": float(confidence) if isinstance(confidence, (float, int)) else state.get("confidence", 0.0),
            }
        return state

    graph.add_node("classify", classify)
    graph.set_entry_point("classify")
    graph.add_edge("classify", END)
    return graph.compile()


def _parse_json(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return None


def _safe_slice(text: str | None) -> str:
    if not text:
        return ""
    return text[:1500]
