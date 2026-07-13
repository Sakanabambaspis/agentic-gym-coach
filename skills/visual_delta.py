"""visual_delta — optional vision-API muscle-group comparison (cloud-gated).

This is the ONLY cloud-bound skill. It compares photos of two dates via a
vision API and reports structured muscle-group changes.

Offline posture (AGENTS.md: full offline operation except optional vision):
  - No provider is selected and no photo-ingestion path exists yet.
  - When GYM_COACH_VISION_API_KEY is unset, return an honest no-data
    VisualDelta (empty changes + a `note`), never fabricated changes.
  - LanceDB stores PATHS + metadata, never raw image blobs.
  - When a provider is configured, wire the call here and cache the diff in
    LanceDB keyed by (date_a, date_b) with `cached=True` on hits.

Contract: no perf target (API-bound). Skippable for offline operation.
"""

from __future__ import annotations

import os
from datetime import date

from models import VisualDelta

_CACHE_COLLECTION = "visual_deltas"

# ponytail: vision provider not selected. When GYM_COACH_VISION_API_KEY exists,
# integrate here (e.g. OpenAI/Anthropic vision), wrap the photo paths from
# LanceDB, cache the structured result, and set cached=True.
_PROVIDER_NOT_SELECTED = not os.environ.get("GYM_COACH_VISION_API_KEY")


def compare_photos(date_a: date, date_b: date) -> VisualDelta:
    if _PROVIDER_NOT_SELECTED:
        return VisualDelta(
            date_a=date_a,
            date_b=date_b,
            muscle_group_changes={},
            cached=False,
            note="vision provider not configured; no photos compared",
        )
    raise NotImplementedError(
        "vision provider integration pending — see skill docstring to wire one"
    )