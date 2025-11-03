from __future__ import annotations
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from .config import FAISS_DIR, EMBEDDING_MODEL, LLM_MODEL, FOLLOWUP_MODEL

_VECTORSTORE = None
_EMBEDDINGS = None
_LLM = None
_FOLLOW_LLM = None

def _require_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Falta OPENAI_API_KEY en el entorno.")

def get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        _require_api_key()
        _EMBEDDINGS = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return _EMBEDDINGS

def get_vectorstore():
    global _VECTORSTORE
    if _VECTORSTORE is None:
        embeddings = get_embeddings()
        if not FAISS_DIR.exists():
            raise FileNotFoundError(f"No existe el directorio del índice: {FAISS_DIR}")
        _VECTORSTORE = FAISS.load_local(
            str(FAISS_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return _VECTORSTORE

def get_llm(temp: float = 0.0):
    global _LLM
    if _LLM is None:
        _require_api_key()
        _LLM = ChatOpenAI(model=LLM_MODEL, temperature=temp)
    return _LLM

def get_follow_llm():
    global _FOLLOW_LLM
    if _FOLLOW_LLM is None:
        _require_api_key()
        _FOLLOW_LLM = ChatOpenAI(model=FOLLOWUP_MODEL, temperature=0)
    return _FOLLOW_LLM
