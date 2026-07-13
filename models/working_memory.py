"""Tier 1 working-memory state — injected into the orchestrator at session start.

MEMORY_PROTOCOL §1: this is RAM, refreshed each session. Holds exactly what
the LLM needs to reason about TODAY: recovery, active injuries, current
phase, and recent specialization context. ~3K-token hard cap (enforced by
the orchestrator via `estimate_tokens()`).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from .enums import MuscleGroup, PhaseType
from .injury import InjuryStatus
from .snapshot import RecoveryScore, TrendReport


class WorkingMemoryState(BaseModel):
    date: date
    recovery: RecoveryScore
    active_injuries: list[InjuryStatus] = Field(default_factory=list)
    phase: PhaseType | None = None
    autoregulation_required: bool = False
    recent_trends: dict[MuscleGroup, TrendReport] = Field(default_factory=dict)

    def estimate_tokens(self) -> int:
        # ponytail: rough proxy ~4 chars/token on JSON. Works for a small object.
        return len(self.model_dump_json()) // 4