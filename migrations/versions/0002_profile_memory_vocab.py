"""v2 — user profile + memory notes; vocabulary pivot (ENUM → VARCHAR).

General-purpose coach pivot:
  - user_profiles: append-only history of Pydantic-validated UserProfile JSON
  - memory_notes: manual-save long-term notes (Tier 3, keyword/tag search)
  - sessions.phase / phase_snapshots.phase / injury_status.location become
    VARCHAR so vocabularies live in models/enums.py (Pydantic boundary), not
    in DDL. Legacy v1 phase values are remapped to the goal-agnostic
    Helms-style vocabulary.

Revision ID: 0002_profile_memory
Revises: 0001_initial
Create Date: 2026-09-09
"""

from alembic import op

revision = "0002_profile_memory"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

# v1 → v2 phase vocabulary (models/enums.PhaseType is the v2 source of truth)
_PHASE_REMAP = """
    CASE CAST(phase AS VARCHAR)
        WHEN 'internship_maintenance' THEN 'maintenance'
        WHEN 'bridge_reconditioning' THEN 'reconditioning'
        WHEN 'specialization_lean_bulk' THEN 'lean_bulk'
        WHEN 'diet_break' THEN 'maintenance'
        WHEN 'mini_cut' THEN 'cut'
        ELSE CAST(phase AS VARCHAR)
    END
"""


def upgrade() -> None:
    # --- sessions.phase: ENUM → VARCHAR with legacy remap ------------------
    op.execute("ALTER TABLE sessions ADD COLUMN phase_v2 VARCHAR")
    op.execute(f"UPDATE sessions SET phase_v2 = {_PHASE_REMAP}")
    op.execute("ALTER TABLE sessions DROP COLUMN phase")
    op.execute("ALTER TABLE sessions RENAME COLUMN phase_v2 TO phase")

    # --- phase_snapshots.phase: ENUM → VARCHAR (same remap) ----------------
    op.execute("ALTER TABLE phase_snapshots ADD COLUMN phase_v2 VARCHAR")
    op.execute(f"UPDATE phase_snapshots SET phase_v2 = {_PHASE_REMAP}")
    op.execute("ALTER TABLE phase_snapshots DROP COLUMN phase")
    op.execute("ALTER TABLE phase_snapshots RENAME COLUMN phase_v2 TO phase")

    # --- injury_status.location: ENUM → VARCHAR (vocab grows in Python) ----
    op.execute("ALTER TABLE injury_status ADD COLUMN location_v2 VARCHAR")
    op.execute("UPDATE injury_status SET location_v2 = CAST(location AS VARCHAR)")
    op.execute("ALTER TABLE injury_status DROP COLUMN location")
    op.execute("ALTER TABLE injury_status RENAME COLUMN location_v2 TO location")

    # --- memory: profile history + manual-save notes ------------------------
    op.execute(
        """
        CREATE TABLE user_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            payload JSON NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE memory_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            kind VARCHAR NOT NULL,
            text TEXT NOT NULL,
            tags VARCHAR[]
        )
        """
    )


def downgrade() -> None:
    # ponytail: lossy by design — v1 enums can't hold the v2 vocabularies.
    # A true downgrade re-imports from the raw log instead.
    op.execute("DROP TABLE IF EXISTS memory_notes")
    op.execute("DROP TABLE IF EXISTS user_profiles")
