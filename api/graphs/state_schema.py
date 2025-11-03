from __future__ import annotations
from typing import List, Dict, TypedDict, Optional
from langchain_core.documents import Document

class RAGState(TypedDict, total=False):
    session_id: str
    question: str
    question_rewritten: str
    followup: bool
    skip_rag: bool
    history: List[Dict]
    history_summary: Optional[str]
    docs: List[Document]
    prompt: str
    answer: str
    sources: List[Dict]
    history_used: bool
