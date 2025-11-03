from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "db" / "chat_history.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn INTEGER NOT NULL,
            role TEXT NOT NULL,         -- 'user' | 'assistant'
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS session_summary (
            session_id TEXT PRIMARY KEY,
            summary TEXT,
            updated_at TEXT NOT NULL
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS rag_answers_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn INTEGER NOT NULL,
            sources_json TEXT NOT NULL,
            contexts_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(session_id, turn)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS rag_evals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn INTEGER NOT NULL,
            faithfulness REAL,
            answer_relevancy REAL,
            context_precision REAL,
            context_recall REAL,
            created_at TEXT NOT NULL,
            UNIQUE(session_id, turn)
        );
        """)
        con.commit()

def load_history(session_id, last_n=8):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT role, message FROM chat_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, last_n))
        rows = cur.fetchall()
    return [{"role": r, "message": m} for (r, m) in rows[::-1]]

def save_turn(session_id, role, message, turn=None):
    with get_conn() as con:
        cur = con.cursor()
        if turn is None:
            cur.execute("""
                SELECT COALESCE(MAX(turn), -1) + 1 
                FROM chat_history WHERE session_id = ?
            """, (session_id,))
            (turn,) = cur.fetchone()
        cur.execute("""
            INSERT INTO chat_history (session_id, turn, role, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, turn, role, message, datetime.utcnow().isoformat()))
        con.commit()
    return turn

def get_summary(session_id):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("SELECT summary FROM session_summary WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
    return row[0] if row else None

def upsert_summary(session_id, summary):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO session_summary (session_id, summary, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                summary = excluded.summary,
                updated_at = excluded.updated_at
        """, (session_id, summary, datetime.utcnow().isoformat()))
        con.commit()

def save_answer_meta(session_id, turn, sources, contexts):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO rag_answers_meta
            (session_id, turn, sources_json, contexts_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            turn,
            json.dumps(sources, ensure_ascii=False),
            json.dumps(contexts, ensure_ascii=False),
            datetime.utcnow().isoformat()
        ))
        con.commit()

def fetch_answers_pending_eval(limit = None):
    """
    Devuelve filas con: session_id, turn, question, answer, sources_json, contexts_json
    solo para respuestas que aún NO han sido evaluadas en rag_evals.
    """
    with get_conn() as con:
        cur = con.cursor()
        sql = """
        SELECT 
            ram.session_id,
            ram.turn,
            (SELECT ch1.message FROM chat_history ch1
                WHERE ch1.session_id = ram.session_id AND ch1.turn = ram.turn AND ch1.role='user' LIMIT 1) AS question,
            (SELECT ch2.message FROM chat_history ch2
                WHERE ch2.session_id = ram.session_id AND ch2.turn = ram.turn AND ch2.role='assistant' LIMIT 1) AS answer,
            ram.sources_json,
            ram.contexts_json
        FROM rag_answers_meta ram
        LEFT JOIN rag_evals re
            ON re.session_id = ram.session_id AND re.turn = ram.turn
        WHERE re.id IS NULL
        ORDER BY ram.id ASC
        """
        if limit:
            sql += " LIMIT ?"
            cur.execute(sql, (limit,))
        else:
            cur.execute(sql)
        rows = cur.fetchall()

    return [
        {
            "session_id": r[0],
            "turn": r[1],
            "question": r[2],
            "answer": r[3],
            "sources_json": r[4],
            "contexts_json": r[5],
        }
        for r in rows
    ]


def save_eval_result(
    session_id,
    turn,
    *,
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
):
    """Guarda resultados de RAGAS en tabla rag_evals."""
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO rag_evals
            (session_id, turn, faithfulness, answer_relevancy, context_precision, context_recall, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, turn,
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            datetime.utcnow().isoformat()
        ))
        con.commit()