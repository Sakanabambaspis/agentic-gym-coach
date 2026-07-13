"""initial schema — enums + sessions, injury_status, phase_snapshots, decision_log

Source of truth: SPEC §1.2. DuckDB-native types:
  - ENUM via CREATE TYPE
  - ARRAY via T[]  (FLOAT[] for reps/rpe; STRUCT(...)[] for exercises)
  - JSON instead of JSONB (DuckDB stores JSON natively)
  - gen_random_uuid() for UUID PKs

Revision ID: 0001_initial
Revises:
Create Date: 2025-07-08
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Controlled vocabularies
    op.execute(
        """
        CREATE TYPE muscle_group AS ENUM (
            'side_delt','rear_delt','upper_chest','mid_back','lats',
            'biceps','triceps','quads','hamstrings','glutes','core','calves','serratus'
        )
        """
    )
    op.execute(
        """
        CREATE TYPE phase_type AS ENUM (
            'internship_maintenance','bridge_reconditioning',
            'specialization_lean_bulk','diet_break','mini_cut','deload'
        )
        """
    )
    op.execute(
        """
        CREATE TYPE pain_location AS ENUM (
            'left_elbow','right_elbow','left_knee','right_knee','lower_back','none'
        )
        """
    )

    op.execute(
        """
        CREATE TABLE sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            date DATE NOT NULL,
            phase phase_type NOT NULL,
            pre_recovery_score INT CHECK (pre_recovery_score BETWEEN 0 AND 100),
            exercises STRUCT(
                name VARCHAR,
                muscle_group muscle_group,
                sets INT,
                reps FLOAT[],
                rpe FLOAT[],
                weight_kg FLOAT[],
                tempo VARCHAR,
                form_quality INT,
                pain_flag BOOLEAN,
                notes TEXT
            )[],
            post_feedback TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE injury_status (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            location pain_location NOT NULL,
            status VARCHAR NOT NULL,
            severity INT CHECK (severity BETWEEN 0 AND 10),
            contraindicated_exercises VARCHAR[],
            safe_alternatives VARCHAR[],
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE phase_snapshots (
            snapshot_date DATE PRIMARY KEY,
            phase phase_type,
            body_weight_kg DECIMAL(5,2),
            waist_cm DECIMAL(5,2),
            specialization_lifts JSON,
            tendon_status_summary JSON,
            key_insight TEXT,
            next_phase_adjustment TEXT
        )
        """
    )

    # Audit trail — SPEC §3.2: log every plan modification + system_error events
    op.execute(
        """
        CREATE TABLE decision_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type VARCHAR NOT NULL,
            trigger_signal TEXT,
            reasoning_chain TEXT,
            alternative_rejected TEXT,
            future_validation_tag TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS decision_log")
    op.execute("DROP TABLE IF EXISTS phase_snapshots")
    op.execute("DROP TABLE IF EXISTS injury_status")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TYPE IF EXISTS pain_location")
    op.execute("DROP TYPE IF EXISTS phase_type")
    op.execute("DROP TYPE IF EXISTS muscle_group")