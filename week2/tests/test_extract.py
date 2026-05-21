import pytest

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ---------------------------------------------------------------------------
# Tests for extract_action_items_llm (TODO 2)
# ---------------------------------------------------------------------------
#
# These tests call a real local Ollama model end-to-end to verify that the
# LLM-powered extractor actually pulls action items out of free-form text.
# They mirror the style of `test_extract_bullets_and_checkboxes` above:
# feed input, then assert that the expected concepts appear in the output.
#
# Because LLM output is not exactly deterministic (wording / casing can
# vary even at temperature=0), we use case-insensitive substring checks on
# the returned items rather than exact-equality matches.
#
# Requires a running Ollama server with the configured model pulled, e.g.:
#     ollama run llama3.2
# ---------------------------------------------------------------------------


def _contains(items, keyword):
    """True if any item contains `keyword` (case-insensitive)."""
    k = keyword.lower()
    return any(k in item.lower() for item in items)


def test_llm_extract_bullet_list():
    text = """
    Notes from meeting:
    - Set up database
    - Implement API extract endpoint
    - Write tests
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) >= 3
    assert _contains(items, "database")
    assert _contains(items, "extract endpoint")
    assert _contains(items, "tests")


def test_llm_extract_keyword_prefixed_lines():
    text = """
    TODO: deploy the staging build
    ACTION: email the design review notes
    NEXT: schedule the retro
    The weather is nice today.
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) >= 3
    assert _contains(items, "staging")
    assert _contains(items, "design review")
    assert _contains(items, "retro")


def test_llm_extract_empty_input():
    assert extract_action_items_llm("") == []
    assert extract_action_items_llm("   \n\t  ") == []


def test_llm_extract_no_actionable_content():
    text = "Today the weather was nice. The sky was blue."
    items = extract_action_items_llm(text)
    # The LLM should recognize that nothing is actionable here.
    assert items == []


def test_llm_extract_mixed_prose_and_bullets():
    text = """
    Hi team,

    Quick recap from today. Alice will own the migration prep.
    A few follow-ups:
    - Fix the failing CI job on master
    - Update the README with the new setup steps

    Also, please remember to file the expense report by Friday.
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) >= 3
    assert _contains(items, "ci") or _contains(items, "failing")
    assert _contains(items, "readme")
    assert _contains(items, "expense")
