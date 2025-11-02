import fitz
import json
import re
import argparse
import string
from unicodedata import normalize

def clean_text(text):
    if not text:
        return ""
    text = normalize("NFKC", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def split_into_paragraphs(text, min_chars):
    paragraphs = re.split(r"\n{2,}|(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in paragraphs if len(p.strip()) > min_chars]

def chunk_paragraphs(paragraphs, max_tokens, overlap):
    chunks = []
    current_chunk = []
    for p in paragraphs:
        words = p.split()
        for w in words:
            current_chunk.append(w)
            if len(current_chunk) >= max_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk = current_chunk[-overlap:]
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def get_hierarchy_for_page(toc, page_num):
    chapter = None
    section = None
    subsection = None
    for level, title, start_page in toc:
        if page_num >= start_page:
            if level == 1:
                chapter = title
                section = None
                subsection = None
            elif level == 2:
                section = title
                subsection = None
            elif level == 3:
                subsection = title
        else:
            break
    return chapter, section, subsection

def is_semantically_useful(text, min_unique_ratio = 0.25, min_alpha_ratio = 0.5, min_length = 80):
    """
    Filtrado permisivo de chunks con bajo contenido semántico.

    - min_unique_ratio: proporción mínima de palabras únicas vs totales.
    - min_alpha_ratio: proporción mínima de caracteres alfabéticos vs totales.
    - min_length: longitud mínima de caracteres.
    """
    if not text or len(text.strip()) < min_length:
        return False

    tokens = text.lower().split()
    if len(tokens) < 5:
        return False

    unique_ratio = len(set(tokens)) / len(tokens)
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    num_ratio = sum(c.isdigit() for c in text) / len(text)
    symbol_ratio = sum(c in string.punctuation for c in text) / len(text)

    if unique_ratio < min_unique_ratio:
        return False
    if alpha_ratio < min_alpha_ratio:
        return False
    if num_ratio > 0.4 or symbol_ratio > 0.3:
        return False

    return True

def process_pdf(input_pdf, output_file, max_tokens, overlap, min_chars):
    doc = fitz.open(input_pdf)
    toc = doc.get_toc()
    output = []

    for page_num in range(1, len(doc)):
        page = doc[page_num]
        raw_text = page.get_text("text")
        clean = clean_text(raw_text)
        if len(clean) < min_chars:
            continue

        chapter, section, subsection = get_hierarchy_for_page(toc, page_num + 1)
        if not chapter or chapter.lower() in ["contents", "index"]:
            continue

        paragraphs = split_into_paragraphs(clean, min_chars)
        chunks = chunk_paragraphs(paragraphs, max_tokens, overlap)

        for i, ch in enumerate(chunks):
            output.append({
                "id": f"page_{page_num+1}_chunk_{i+1}",
                "page": page_num + 1,
                "chapter": chapter,
                "section": section,
                "subsection": subsection,
                "text": ch
            })

    filtered_output = [c for c in output if is_semantically_useful(c["text"])]
    removed_output = [c for c in output if not is_semantically_useful(c["text"])]

    print(f"Chunks totales: {len(output)} | Útiles: {len(filtered_output)} | Eliminados: {len(removed_output)}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_output, f, ensure_ascii=False, indent=2)

    removed_file = output_file.replace(".json", "_removed.json")
    with open(removed_file, "w", encoding="utf-8") as f:
        json.dump(removed_output, f, ensure_ascii=False, indent=2)

    print(f"PDF procesado: {len(filtered_output)} chunks útiles guardados en {output_file}")
    print(f"Chunks eliminados guardados en {removed_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesa un PDF y genera chunks limpios para RAG.")
    parser.add_argument("--input_pdf", type=str, default="data/raw/PDF-GenAI-Challenge.pdf", help="Ruta del PDF de entrada.")
    parser.add_argument("--output_json", type=str, default="data/processed/clean_chunks.json", help="Ruta del archivo JSON de salida.")
    parser.add_argument("--max_tokens", type=int, default=800, help="Número máximo de tokens por chunk.")
    parser.add_argument("--overlap", type=int, default=160, help="Número de tokens de solapamiento entre chunks.")
    parser.add_argument("--min_chars", type=int, default=50, help="Número mínimo de caracteres para considerar un párrafo.")

    args = parser.parse_args()

    process_pdf(
        input_pdf=args.input_pdf,
        output_file=args.output_json,
        max_tokens=args.max_tokens,
        overlap=args.overlap,
        min_chars=args.min_chars,
    )