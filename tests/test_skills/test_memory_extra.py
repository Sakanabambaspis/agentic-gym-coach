"""memory (Tier 3) edge cases — validation, AND-semantics, limits, ordering."""

import pytest

from models import NoteKind
from skills.memory import add_note, search_notes


def test_empty_and_whitespace_text_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        add_note("")
    with pytest.raises(ValueError, match="cannot be empty"):
        add_note("   ")


def test_unknown_kind_rejected_at_vocabulary():
    with pytest.raises(ValueError):
        NoteKind("banana")


def test_text_is_stripped_on_write():
    note = add_note("  prefers chest-supported rows  ")
    assert note.text == "prefers chest-supported rows"


def test_substring_search_is_case_insensitive():
    add_note("Prefers CHEST-SUPPORTED rows over barbell rows")
    hits = search_notes(query="chest-supported")
    assert len(hits) == 1


def test_tag_search_matches_any_given_tag():
    add_note("note one", tags=["preference", "rows"])
    add_note("note two", tags=["milestone"])
    hits = search_notes(tags=["milestone", "nonexistent"])
    assert [n.text for n in hits] == ["note two"]


def test_query_and_tags_combine_with_and():
    add_note("hates barbell rows", tags=["preference"])
    add_note("hates barbell rows", tags=["milestone"])
    hits = search_notes(query="barbell", tags=["milestone"])
    assert len(hits) == 1
    assert hits[0].tags == ["milestone"]


def test_no_match_returns_empty_list():
    assert search_notes(query="does-not-exist-anywhere") == []


def test_limit_returns_newest_first():
    add_note("first")
    add_note("second")
    hits = search_notes(limit=1)
    assert len(hits) == 1 and hits[0].text == "second"
