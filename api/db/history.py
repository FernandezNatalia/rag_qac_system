from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

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
        con.commit()

def load_history(session_id, last_n = 8):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT role, message FROM chat_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, last_n))
        rows = cur.fetchall()
    turns = [{"role": r, "message": m} for (r, m) in rows[::-1]]
    return turns

def save_turn(session_id, role, message, turn = None):
    with get_conn() as con:
        cur = con.cursor()
        if turn is None:
            cur.execute("SELECT COALESCE(MAX(turn), -1) + 1 FROM chat_history WHERE session_id = ?", (session_id,))
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
