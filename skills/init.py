"""DB connection helpers — single source for DuckDB + LanceDB handles.

Persistent file mode (SPEC §1.1):
  - DuckDB: data/gym_coach.duckdb
  - LanceDB: data/lance_db/

A module-level cache keeps one connection per process. Skills call
get_duckdb()/get_lance() instead of opening their own — avoids locking
fights and keeps the close path in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import lancedb

# ponytail: process-global singletons. DB file is single-writer anyway,
# so parallel connections buy nothing here. Swap for a pool if concurrent
# writers ever show up.
_duck: duckdb.DuckDBPyConnection | None = None
_lance: Any = None  # lancedb.LanceDBConnection — typed loosely for import cheapness

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DUCK_PATH = Path(os.environ.get("GYM_COACH_DUCKDB", _REPO_ROOT / "data" / "gym_coach.duckdb"))
_LANCE_PATH = Path(os.environ.get("GYM_COACH_LANCE", _REPO_ROOT / "data" / "lance_db"))


def get_duckdb() -> duckdb.DuckDBPyConnection:
    """Return the shared DuckDB connection (creates the file on first call)."""
    global _duck
    if _duck is None:
        _DUCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        _duck = duckdb.connect(str(_DUCK_PATH))
    return _duck


def get_lance():
    """Return the shared LanceDB connection (creates the dir on first call)."""
    global _lance
    if _lance is None:
        _LANCE_PATH.mkdir(parents=True, exist_ok=True)
        _lance = lancedb.connect(str(_LANCE_PATH))
    return _lance


def close_all() -> None:
    """Close shared connections — call at process exit / tests teardown."""
    global _duck, _lance
    if _duck is not None:
        _duck.close()
        _duck = None
    _lance = None