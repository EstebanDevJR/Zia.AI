from app.agent.graph import build_graph


def summarize_text(text: str) -> str:
    graph = build_graph()
    result = graph.invoke({"text": text, "summary": ""})
    return result["summary"]
