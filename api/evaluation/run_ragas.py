from __future__ import annotations
import argparse
import asyncio
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ..graphs.config import EMBEDDING_MODEL, EVALUATOR_MODEL
from ..db.history import (
    fetch_answers_pending_eval,
    save_eval_result,
)
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import (
    Faithfulness, 
    LLMContextPrecisionWithoutReference, 
    LLMContextRecall, 
    ResponseRelevancy
)

load_dotenv()

def build_samples(rows):
    samples = []
    for r in rows:
        contexts = json.loads(r["contexts_json"]) or []
        
        retrieved = [str(c) for c in contexts if c]

        samples.append(
            SingleTurnSample(
                user_input=r["question"],
                response=r["answer"],
                retrieved_contexts=retrieved,
                reference="\n\n".join(retrieved)
            )
        )
    return samples


async def run_eval(limit, dry_run):
    rows = fetch_answers_pending_eval(limit=limit)
    if not rows:
        message = "No hay respuestas pendientes de evaluación."
        print(message)
        return {
            "requested": 0,
            "evaluated": 0,
            "dry_run": dry_run,
            "errors": [],
            "message": message,
        }

    total = len(rows)
    print(f"Evaluando {total} respuestas...")

    evaluator_llm = ChatOpenAI(model=EVALUATOR_MODEL, temperature=0, model_kwargs={
        "response_format": {"type": "json_object"}
    })
    evaluator_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    faithfulness_metric = Faithfulness(llm=evaluator_llm)
    precision_metric = LLMContextPrecisionWithoutReference(llm=evaluator_llm)
    recall_metric = LLMContextRecall(llm=evaluator_llm)
    relevancy_metric = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)

    samples = build_samples(rows)

    evaluated = 0
    errors = []

    for idx, r in enumerate(rows):

        print(f"\n--- [{r['session_id']} - turn {r['turn']}] ---")

        scores = {}

        try:
            scores["faithfulness"] = await faithfulness_metric.single_turn_ascore(samples[idx])
            scores["context_precision"] = await precision_metric.single_turn_ascore(samples[idx])
            scores["answer_relevancy"] = await relevancy_metric.single_turn_ascore(samples[idx])
            scores["context_recall"] = await recall_metric.single_turn_ascore(samples[idx])

            print(json.dumps(scores, indent=2, ensure_ascii=False))

            if not dry_run:
                save_eval_result(
                    r["session_id"],
                    r["turn"],
                    faithfulness=scores.get("faithfulness"),
                    answer_relevancy=scores.get("answer_relevancy"),
                    context_precision=scores.get("context_precision"),
                    context_recall=scores.get("context_recall")
                )
            evaluated += 1

        except Exception as e:
            error_msg = f"Error evaluando sesión {r['session_id']}, turn {r['turn']}: {e}"
            print(error_msg)
            errors.append(
                {
                    "session_id": r["session_id"],
                    "turn": r["turn"],
                    "error": str(e),
                }
            )

    if dry_run:
        print("\nDRY RUN activado → no se guardaron resultados.")
    else:
        print("\nEvaluaciones guardadas correctamente.")

    return {
        "requested": total,
        "evaluated": evaluated,
        "dry_run": dry_run,
        "errors": errors,
        "message": (
            "DRY RUN activado → no se guardaron resultados."
            if dry_run
            else "Evaluaciones guardadas correctamente."
        ),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Cantidad máxima de respuestas a evaluar")
    parser.add_argument("--dry-run", action="store_true", help="Evalúa pero NO graba en la base")
    args = parser.parse_args()

    asyncio.run(run_eval(limit=args.limit, dry_run=args.dry_run))

if __name__ == "__main__":
    main()