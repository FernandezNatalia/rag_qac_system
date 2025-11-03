from __future__ import annotations
from ..resources import get_llm
from api.db.history import upsert_summary
from api.graphs.prompts.summarize_history import SUMMARIZE_HISTORY_PROMPT
from ..config import MAX_CONTEXT_CHARS

def summarize_history_node(state):
    sid = state["session_id"]

    total_chars = (
        sum(len(x["message"]) for x in state.get("history", []))
        + len(state.get("answer", ""))
    )

    if total_chars < MAX_CONTEXT_CHARS:
        return {}

    raw = "\n".join(
        (("U: " + t["message"]) if t["role"] == "user" else ("A: " + t["message"]))
        for t in state.get("history", [])
    )

    llm = get_llm()
    prompt = SUMMARIZE_HISTORY_PROMPT.format(conversation=raw)
    out = llm.invoke(prompt)

    summary = getattr(out, "content", "").strip()
    if summary:
        upsert_summary(sid, summary)

    return {"history_summary": summary}
