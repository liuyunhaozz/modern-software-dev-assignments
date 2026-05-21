"""SQLite persistence layer.

Each helper opens a short-lived connection, runs a single transaction,
and returns plain Python data (no `sqlite3.Row` objects leak out to
callers). Foreign-key constraints are enabled on every connection so the
`action_items.note_id` reference is actually enforced.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

from .config import get_settings


# ---------- Schema ---------------------------------------------------------

_CREATE_NOTES_TABLE = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_CREATE_ACTION_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER,
    text TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);
"""


# ---------- Connection management -----------------------------------------


def _ensure_data_directory() -> None:
    get_settings().data_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with foreign keys enabled.

    Commits on clean exit, rolls back on exception, and always closes
    the underlying handle.
    """
    _ensure_data_directory()
    conn = sqlite3.connect(get_settings().db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.execute(_CREATE_NOTES_TABLE)
        conn.execute(_CREATE_ACTION_ITEMS_TABLE)


# ---------- Row -> dict adapters ------------------------------------------


def _note_row(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "content": row["content"], "created_at": row["created_at"]}


def _action_item_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "note_id": row["note_id"],
        "text": row["text"],
        "done": bool(row["done"]),
        "created_at": row["created_at"],
    }


# ---------- Notes ----------------------------------------------------------


def insert_note(content: str) -> int:
    with connection() as conn:
        cursor = conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        return int(cursor.lastrowid)


def list_notes() -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return [_note_row(r) for r in rows]


def get_note(note_id: int) -> Optional[dict]:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        ).fetchone()
    return _note_row(row) if row else None


# ---------- Action items ---------------------------------------------------


def insert_action_items(items: list[str], note_id: Optional[int] = None) -> list[int]:
    if not items:
        return []
    with connection() as conn:
        ids: list[int] = []
        for item in items:
            cursor = conn.execute(
                "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                (note_id, item),
            )
            ids.append(int(cursor.lastrowid))
        return ids


def list_action_items(note_id: Optional[int] = None) -> list[dict]:
    with connection() as conn:
        if note_id is None:
            rows = conn.execute(
                "SELECT id, note_id, text, done, created_at "
                "FROM action_items ORDER BY id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, note_id, text, done, created_at "
                "FROM action_items WHERE note_id = ? ORDER BY id DESC",
                (note_id,),
            ).fetchall()
    return [_action_item_row(r) for r in rows]


def get_action_item(action_item_id: int) -> Optional[dict]:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, note_id, text, done, created_at "
            "FROM action_items WHERE id = ?",
            (action_item_id,),
        ).fetchone()
    return _action_item_row(row) if row else None


def mark_action_item_done(action_item_id: int, done: bool) -> bool:
    """Return True if a row was updated, False if the id did not exist."""
    with connection() as conn:
        cursor = conn.execute(
            "UPDATE action_items SET done = ? WHERE id = ?",
            (1 if done else 0, action_item_id),
        )
        return cursor.rowcount > 0
