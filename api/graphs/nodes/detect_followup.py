from __future__ import annotations
from ..resources import get_follow_llm
from ..prompts.detect_followup import DETECT_FOLLOWUP_PROMPT

def detect_followup_node(state):
    llm = get_follow_llm()

    history = ""
    if state.get("history"):
        history = "\n".join(
            ("U: " + t["message"] if t["role"] == "user" else "A: " + t["message"])
            for t in state["history"]
        )

    prompt = DETECT_FOLLOWUP_PROMPT.format(
        history=history, 
        question=state["question"]
    )

    out = llm.invoke(prompt)
    label = getattr(out, "content", "").strip().lower()

    if label == "smalltalk":
        return {"skip_rag": True, "followup": False}

    return {"skip_rag": False, "followup": (label == "followup")}
