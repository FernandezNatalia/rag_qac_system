from __future__ import annotations
from ..resources import get_vectorstore, get_llm
from ..config import TOP_K, MAX_CONTEXT_CHARS
from api.graphs.prompts.rag_answer import (
    RAG_ANSWER_SYSTEM_PROMPT,
    RAG_ANSWER_USER_PROMPT,
)

def _format_prompt(question, rewritten, docs, history_summary):
    context_blocks = []
    for i, d in enumerate(docs, 1):
        content = d.page_content.strip()
        if len(content) > MAX_CONTEXT_CHARS:
            content = content[:MAX_CONTEXT_CHARS] + "\n[...]"

        m = d.metadata or {}
        header = f"(Fuente {i} | pág {m.get('page')} | cap {m.get('chapter')})"
        context_blocks.append(f"{header}\n{content}")

    context = "\n\n".join(context_blocks)
    history_block = (
        f"\n[Resumen de historial]\n{history_summary}\n"
        if history_summary else ""
    )

    return (
        RAG_ANSWER_SYSTEM_PROMPT
        + "\n\n"
        + RAG_ANSWER_USER_PROMPT.format(
            question=question,
            rewritten=rewritten,
            history_block=history_block,
            context=context
        )
    )

def rag_pipeline_node(state):
    vs = get_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": TOP_K})

    rewritten = state.get("question_rewritten") or state["question"]
    docs = retriever.invoke(rewritten)

    prompt = _format_prompt(
        question=state["question"],
        rewritten=rewritten,
        docs=docs or [],
        history_summary=state.get("history_summary"),
    )

    llm = get_llm()
    out = llm.invoke(prompt)
    answer = getattr(out, "content", str(out))

    sources = []
    for d in docs or []:
        m = d.metadata or {}
        sources.append({
            "id": m.get("id"),
            "page": m.get("page"),
            "chapter": m.get("chapter"),
            "section": m.get("section"),
            "subsection": m.get("subsection"),
        })

    return {
        "answer": answer,
        "sources": sources
    }
