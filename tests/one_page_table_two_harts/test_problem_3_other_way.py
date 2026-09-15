"""Checks Problem 6.3 against the chapter's own committed run, so the reversal is measured."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.one_page_table_two_harts.problem_3_other_way import WHICH_INSTRUCTION_MOVED

ANSWER = Path(__file__).parent / "answer_other.c"


def test_the_chapter_loses_exactly_one_update():
    """Scaffolding: the behaviour being reversed is deterministic, so a reversal is checkable."""
    summary = load_result("harts-bare")["summary"]
    assert summary["updates_lost"] == 1
    assert summary["counter_after"] == 1


@pytest.mark.problem
def test_the_other_hart_is_the_one_that_lost(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 6.3: put your program in {ANSWER.name} beside this test"

    source = ANSWER.read_text()
    assert "bare_secondary" in source, "the program still needs a second hart"

    image = bare.build_from([ANSWER], "problem_other", build_dir=tmp_path)
    fields = bare.run("harts", image=image, harts=2, timeout=30).fields()
    assert fields.get("counter_after") == 1, "the counter no longer ends where the chapter's does"
    assert fields.get("updates_lost") == 1, "exactly one update should still go missing"
    assert fields.get("lost_from_hart") == 0, (
        "the update that went missing is still the second hart's, which is what the chapter "
        "already showed — the problem asks for the first hart's"
    )


@pytest.mark.problem
def test_the_reader_named_the_instruction_that_moved():
    assert WHICH_INSTRUCTION_MOVED.strip().lower() in {"load", "add", "store"}, (
        "Problem 6.3: WHICH_INSTRUCTION_MOVED should name one of the three"
    )
