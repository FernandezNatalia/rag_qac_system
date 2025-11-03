from __future__ import annotations
from api.db.history import save_turn, load_history, get_summary

def load_history_node(state):
    session_id = state["session_id"]
    hist = load_history(session_id, last_n=8)
    summary = get_summary(session_id)
    return {"history": hist, "history_summary": summary or ""}

def save_history_node(state):
    sid = state["session_id"]
    turn = save_turn(sid, "user", state["question"])
    save_turn(sid, "assistant", state.get("answer", ""), turn=turn)
    return {}