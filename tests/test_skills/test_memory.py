"""memory unit tests — add, substring search, tag search, empty rejection."""

import pytest

from models import NoteKind
from skills.memory import add_note, search_notes


def test_add_and_search_by_substring():
    add_note("User prefers chest-supported rows over barbell rows", kind=NoteKind.preference)
    add_note("First 10 strict pull-ups completed", kind=NoteKind.milestone)
    hits = search_notes(query="pull-ups")
    assert len(hits) == 1
    assert hits[0].kind == NoteKind.milestone
    assert hits[0].id is not None


def test_search_case_insensitive():
    add_note("Elbow tolerates neutral-grip PUSHDOWNs well")
    assert len(search_notes(query="pushdowns")) == 1


def test_search_by_tag():
    add_note("responds well to high frequency", tags=["delts", "volume"])
    add_note("dislikes barbells", tags=["equipment"])
    assert len(search_notes(tags=["delts"])) == 1
    assert len(search_notes(tags=["equipment"])) == 1


def test_search_no_filters_returns_all_limited():
    for i in range(5):
        add_note(f"note {i}")
    assert len(search_notes(limit=3)) == 3


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        add_note("   ")
