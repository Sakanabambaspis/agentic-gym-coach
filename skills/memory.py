"""memory — manual-save long-term notes (MEMORY_PROTOCOL Tier 3).

Deliberately deterministic and offline: DuckDB keyword/tag search, no
embeddings. LanceDB semantic search is a future upgrade; until then this
store honors the same write policy — Tier 3 writes require an explicit user
command ("save this"); the skill itself cannot verify intent, so the policy
is enforced procedurally by the coach prompt, not here.

Contract: add_note returns the persisted note; search_notes matches
case-insensitive substring + any-tag. Never auto-writes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from models import MemoryNote, NoteKind

from .init import get_duckdb


def add_note(text: str, kind: NoteKind = NoteKind.observation,
             tags: list[str] | None = None) -> MemoryNote:
    if not text.strip():
        raise ValueError("note text cannot be empty")
    row = get_duckdb().execute(
        """
        INSERT INTO memory_notes (created_at, kind, text, tags)
        VALUES (?, ?, ?, ?)
        RETURNING id, created_at
        """,
        [datetime.now(timezone.utc), kind.value, text.strip(), tags or []],
    ).fetchone()
    return MemoryNote(id=row[0], created_at=row[1], kind=kind,
                      text=text.strip(), tags=tags or [])


def search_notes(query: str | None = None, tags: list[str] | None = None,
                 limit: int = 20) -> list[MemoryNote]:
    """Notes matching (substring query) AND (any of the given tags)."""
    sql = "SELECT id, created_at, kind, text, tags FROM memory_notes"
    conds, params = [], []
    if query:
        conds.append(" strpos(lower(text), lower(?)) > 0 ")
        params.append(query)
    if tags:
        conds.append(" len(list_intersect(tags, ?::VARCHAR[])) > 0 ")
        params.append(tags)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = get_duckdb().execute(sql, params).fetchall()
    return [
        MemoryNote(
            id=r[0], created_at=r[1], kind=NoteKind(r[2]), text=r[3], tags=list(r[4] or [])
        )
        for r in rows
    ]
