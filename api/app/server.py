from __future__ import annotations
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api.db.history import init_db
from api.graphs.graph import build_rag_graph
from langserve import add_routes
import uvicorn
import traceback

load_dotenv()
init_db()

app = FastAPI(title="RAG Chatbot")

graph_app = build_rag_graph()
add_routes(app, graph_app, path="/graph")

class ChatRequest(BaseModel):
    session_id: str
    question: str

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        app = build_rag_graph()
        result = app.invoke({"session_id": req.session_id, "question": req.question})
        return {
            "answer": result.get("answer", ""),
            "question_rewritten": result.get("question_rewritten", req.question),
            "followup": result.get("followup", False),
            "skip_rag": result.get("skip_rag", False),
            "sources": result.get("sources", []),
            "history_used": bool(result.get("history_used"))
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)