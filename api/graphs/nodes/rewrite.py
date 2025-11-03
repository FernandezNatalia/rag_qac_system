from __future__ import annotations
from ..resources import get_llm
from ..prompts.rewrite_query import REWRITE_QUERY_PROMPT


def rewrite_query_node(state):
    if not state.get("followup"):
        return {"question_rewritten": state["question"], "history_used": False}

    llm = get_llm()
    history_text = ""
    if state.get("history_summary"):
        history_text += f"[Resumen]\n{state['history_summary']}\n\n"
    if state.get("history"):
        history_text += "[Últimos turnos]\n" + "\n".join(
            (("U: " + t["message"]) if t["role"] == "user" else ("A: " + t["message"]))
            for t in state["history"]
        )

    prompt = REWRITE_QUERY_PROMPT.format(
        history_text=history_text,
        question=state["question"]
    )

    out = llm.invoke(prompt)
    rewritten = getattr(out, "content", "").strip()

    return {
        "question_rewritten": rewritten,
        "history_used": rewritten != state["question"]
    }
