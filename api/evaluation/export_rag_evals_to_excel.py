import sqlite3
import pandas as pd
from pathlib import Path
from ..db.history import DB_PATH

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SCRIPT_DIR / "excel_results" / "rag_evals.xlsx"

def export_to_excel():
    print(f"Leyendo base de datos desde: {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            re.session_id,
            re.turn,
            re.faithfulness,
            re.answer_relevancy,
            re.context_precision,
            re.context_recall,
            re.created_at,
            (SELECT ch1.message FROM chat_history ch1
                WHERE ch1.session_id = re.session_id AND ch1.turn = re.turn AND ch1.role='user' LIMIT 1) AS question,
            (SELECT ch2.message FROM chat_history ch2
                WHERE ch2.session_id = re.session_id AND ch2.turn = re.turn AND ch2.role='assistant' LIMIT 1) AS answer
        FROM rag_evals re
        ORDER BY re.created_at ASC
    """
    df = pd.read_sql_query(query, con)
    con.close()

    print(f"{len(df)} filas cargadas.")

    df.to_excel(OUTPUT_FILE, index=False)

    print(f"Archivo generado: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    export_to_excel()
