from __future__ import annotations
from api.db.history import save_turn, load_history, get_summary, save_answer_meta

def load_history_node(state):
    session_id = state["session_id"]
    hist = load_history(session_id, last_n=8)
    summary = get_summary(session_id)
    return {"history": hist, "history_summary": summary or ""}

def save_history_node(state):
    sid = state["session_id"]
    turn = save_turn(sid, "user", state["question"])
    save_turn(sid, "assistant", state.get("answer", ""), turn=turn)

    sources = state.get("sources") or []
    contexts = []
    for d in (state.get("docs") or []):
        try:
            contexts.append(d.page_content)
        except Exception:
            pass

    if sources or contexts:
        save_answer_meta(sid, turn, sources, contexts)

    return {}