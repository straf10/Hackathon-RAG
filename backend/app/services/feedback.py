import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)

_DB_PATH: Path = settings.FEEDBACK_DB_DIR / "feedback.db"
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=DELETE")
        _conn.execute("PRAGMA foreign_keys=ON")
        _init_tables(_conn)
        logger.info("Feedback database initialised at %s", _DB_PATH)
    return _conn


def _init_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id TEXT PRIMARY KEY,
            query_id    TEXT    NOT NULL,
            rating      TEXT    NOT NULL CHECK(rating IN ('up', 'down')),
            comment     TEXT,
            created_at  TEXT    NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_query_id ON feedback(query_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at)"
    )
    conn.commit()


def save_feedback(
    feedback_id: str,
    query_id: str,
    rating: str,
    comment: str | None,
) -> None:
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO feedback (feedback_id, query_id, rating, comment, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (feedback_id, query_id, rating, comment, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    logger.info("Feedback persisted: id=%s query=%s rating=%s", feedback_id, query_id, rating)


def get_feedback_stats() -> dict[str, Any]:
    conn = _get_conn()
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                    AS total_queries,
            COALESCE(SUM(rating = 'up'),   0)           AS thumbs_up,
            COALESCE(SUM(rating = 'down'), 0)           AS thumbs_down
        FROM feedback
        """
    ).fetchone()
    total = row["total_queries"]
    thumbs_up = row["thumbs_up"]
    thumbs_down = row["thumbs_down"]
    positive_pct = round(100.0 * thumbs_up / total, 2) if total else 0.0
    negative_pct = round(100.0 * thumbs_down / total, 2) if total else 0.0
    return {
        "total_queries": total,
        "positive_percentage": positive_pct,
        "negative_percentage": negative_pct,
    }


def get_recent_feedback(limit: int = 20) -> list[dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT feedback_id, query_id, rating, comment, created_at
        FROM feedback
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
