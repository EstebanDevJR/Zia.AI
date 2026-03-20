from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings


class SummaryState(TypedDict):
    text: str
    summary: str


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0.2)


def build_graph():
    graph = StateGraph(SummaryState)

    def summarize(state: SummaryState) -> SummaryState:
        if not settings.openai_api_key:
            summary = _fallback_summary(state["text"])
            return {"text": state["text"], "summary": summary}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Eres un analista de noticias de IA. Resume en 3-4 frases, "
                    "en español, sin inventar datos."
                ),
                ("human", "{text}"),
            ]
        )
        chain = prompt | _llm() | StrOutputParser()
        summary = chain.invoke({"text": state["text"]})
        return {"text": state["text"], "summary": summary.strip()}

    def polish(state: SummaryState) -> SummaryState:
        if not settings.openai_api_key:
            return state

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Reescribe el resumen para que sea claro, directo y sin hype."
                ),
                ("human", "{text}"),
            ]
        )
        chain = prompt | _llm() | StrOutputParser()
        summary = chain.invoke({"text": state["summary"]})
        return {"text": state["text"], "summary": summary.strip()}

    graph.add_node("summarize", summarize)
    graph.add_node("polish", polish)
    graph.set_entry_point("summarize")
    graph.add_edge("summarize", "polish")
    graph.add_edge("polish", END)

    return graph.compile()


def _fallback_summary(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= 320:
        return clean
    return clean[:320].rsplit(" ", 1)[0] + "..."
