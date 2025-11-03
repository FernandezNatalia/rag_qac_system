from __future__ import annotations
from ..prompts.smalltalk import SMALLTALK_PROMPT
from ..resources import get_llm

def smalltalk_node(state):
    llm = get_llm(temp=0.7)
    text = state["question"]
    prompt = SMALLTALK_PROMPT.format(text=text)
    out = llm.invoke(prompt)

    return {
        "skip_rag": True,
        "followup": False,
        "question_rewritten": state["question"],
        "answer": getattr(out, "content", "").strip(),
        "sources": [],
        "history_used": False
    }
