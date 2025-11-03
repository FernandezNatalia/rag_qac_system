from __future__ import annotations
from langgraph.graph import StateGraph, END
from .state_schema import RAGState
from .nodes.history import load_history_node
from .nodes.detect_followup import detect_followup_node
from .nodes.smalltalk import smalltalk_node
from .nodes.rewrite import rewrite_query_node
from .nodes.rag_pipeline import rag_pipeline_node
from .nodes.history import save_history_node
from .nodes.summarize_history import summarize_history_node

def to_smalltalk(state):
    return "smalltalk" if state.get("skip_rag") else "rewrite_query"

def build_rag_graph():
    graph = StateGraph(RAGState)

    graph.add_node("load_history", load_history_node)
    graph.add_node("detect_followup", detect_followup_node)
    graph.add_node("smalltalk", smalltalk_node)
    graph.add_node("rewrite_query", rewrite_query_node)
    graph.add_node("rag_pipeline", rag_pipeline_node)
    graph.add_node("save_history", save_history_node)
    graph.add_node("summarize_history", summarize_history_node)

    graph.set_entry_point("load_history")
    graph.add_edge("load_history", "detect_followup")
    graph.add_conditional_edges("detect_followup", to_smalltalk, {
        "smalltalk": "smalltalk",
        "rewrite_query": "rewrite_query"
    })
    graph.add_edge("smalltalk", "save_history")
    graph.add_edge("rewrite_query", "rag_pipeline")
    graph.add_edge("rag_pipeline", "save_history")
    graph.add_edge("save_history", "summarize_history")
    graph.add_edge("summarize_history", END)

    return graph.compile()
