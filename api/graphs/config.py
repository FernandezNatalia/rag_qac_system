from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FAISS_DIR = PROJECT_ROOT / "api" / "vector_store"
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4.1-mini"
FOLLOWUP_MODEL = "gpt-4.1-mini"
TOP_K = 6
SCORE_THRESHOLD = 0.25
LANG = "ES"
MAX_CONTEXT_CHARS = 5000