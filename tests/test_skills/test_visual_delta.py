"""visual_delta unit tests — offline returns honest no-data delta; never fabricates.

The real vision-API path is gated behind GYM_COACH_VISION_API_KEY and has no
provider wired yet. Tests pin the offline behavior so the skill stays
offline-safe and never invents muscle-group changes.
"""

from datetime import date

import pytest

from skills.visual_delta import compare_photos


def test_offline_returns_no_data_delta():
    d = compare_photos(date(2025, 1, 1), date(2025, 2, 1))
    assert d.date_a == date(2025, 1, 1)
    assert d.date_b == date(2025, 2, 1)
    assert d.muscle_group_changes == {}
    assert d.cached is False
    assert d.note != ""  # honest reason, not silent


def test_offline_never_fabricates_changes():
    d = compare_photos(date(2025, 1, 1), date(2025, 2, 1))
    assert d.muscle_group_changes == {}


def test_same_date_pair_is_valid():
    d = compare_photos(date(2025, 1, 1), date(2025, 1, 1))
    assert d.cached is False