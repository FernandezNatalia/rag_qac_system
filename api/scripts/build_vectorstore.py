import argparse
import json
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()

def enrich_text_for_embedding(item):
    chapter = item.get("chapter") or "N/A"
    section = item.get("section") or "N/A"
    subsection = item.get("subsection") or "N/A"

    meta = (
        f"### Metadata\n"
        f"- Chapter: {chapter}\n"
        f"- Section: {section}\n"
        f"- Subsection: {subsection}\n"
        f"### Content\n"
    )
    return f"{meta}{item.get('text','').strip()}"

def load_chunks(json_path, min_chars=30):
    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    docs = [
        Document(
            page_content=enrich_text_for_embedding(item),
            metadata={
                "id": item["id"],
                "page": item.get("page"),
                "chapter": item.get("chapter"),
                "section": item.get("section"),
                "subsection": item.get("subsection"),
            }
        )
        for item in raw_data
        if item.get("text") and len(item["text"].strip()) > min_chars
    ]

    return docs

def main():
    parser = argparse.ArgumentParser(description="Construye índice FAISS con embeddings OpenAI")
    parser.add_argument("--input", type=str, default="data/processed/clean_chunks.json")
    parser.add_argument("--output", type=str, default="vector_store")
    parser.add_argument("--model", type=str, default="text-embedding-3-large")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--min-chars", type=int, default=40)
    parser.add_argument("--force", action="store_true", help="sobrescribir si ya existe el índice")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {input_path}")

    if output_dir.exists() and not args.force:
        print(f"El índice ya existe en: {output_dir}")
        print("Usa --force para sobrescribir.")
        return

    docs = load_chunks(input_path, args.min_chars)
    embeddings = OpenAIEmbeddings(model=args.model)

    vectorstore = None
    for i in tqdm(range(0, len(docs), args.batch_size), desc="Procesando batches"):
        batch = docs[i:i + args.batch_size]
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            vectorstore.add_documents(batch)

    output_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(output_dir)

    print(f"\nÍndice FAISS guardado en: {output_dir}")

if __name__ == "__main__":
    main()
