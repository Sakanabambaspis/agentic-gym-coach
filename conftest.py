"""pytest rootdir anchor + test DB isolation.

Tests run against a throwaway DuckDB file (NOT the production
data/gym_coach.duckdb), with the schema applied once per session. Set via
env vars read by skills.init BEFORE any test imports it. The production DB
and its backfilled sessions are never touched by the test suite.

ponytail: single-process pytest only. Concurrent pytest-xdist workers would
collide on the shared temp file — add per-worker temp paths if that matters.
"""

import os
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent
_TEST_DUCK = Path(tempfile.gettempdir()) / "gym_coach_test.duckdb"
_TEST_LANCE = Path(tempfile.gettempdir()) / "gym_coach_test_lance"

# Set BEFORE skills.init is imported anywhere.
os.environ["GYM_COACH_DUCKDB"] = str(_TEST_DUCK)
os.environ.setdefault("GYM_COACH_LANCE", str(_TEST_LANCE))


@pytest.fixture(scope="session", autouse=True)
def _init_test_schema():
    """Apply the full schema to the temp DB once per session."""
    from alembic import command
    from alembic.config import Config

    _TEST_DUCK.unlink(missing_ok=True)
    cfg = Config(str(_REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"duckdb:///{_TEST_DUCK}")
    command.upgrade(cfg, "head")
    yield
    # leave the temp file; OS temp cleanup handles it eventually


@pytest.fixture(autouse=True)
def _clean_tables():
    """Wipe the data tables before+after every test so results don't bleed."""
    from skills.init import get_duckdb

    d = get_duckdb()
    d.execute("DELETE FROM sessions")
    d.execute("DELETE FROM injury_status")
    d.execute("DELETE FROM decision_log")
    d.execute("DELETE FROM phase_snapshots")
    d.execute("DELETE FROM user_profiles")
    d.execute("DELETE FROM memory_notes")
    yield
    d = get_duckdb()
    d.execute("DELETE FROM sessions")
    d.execute("DELETE FROM injury_status")
    d.execute("DELETE FROM decision_log")
    d.execute("DELETE FROM phase_snapshots")
    d.execute("DELETE FROM user_profiles")
    d.execute("DELETE FROM memory_notes")