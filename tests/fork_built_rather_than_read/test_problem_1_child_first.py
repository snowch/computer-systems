"""Checks Problem 9.1 by running the reader's program: the order changed, the results did not."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.fork_built_rather_than_read.problem_1_child_first import WHAT_HAS_TO_BE_SAVED

ANSWER = Path(__file__).parent / "answer_child_first.c"


def test_the_chapters_fork_returned_two_answers():
    """Scaffolding: the behaviour that must survive the reordering."""
    summary = load_result("fork-bare")["summary"]
    assert summary["results_differ"] == 1
    assert summary["both_ran"] == 1


@pytest.mark.problem
def test_the_child_finished_first_and_nothing_else_changed(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 9.1: put your program in {ANSWER.name} beside this test"

    committed = load_result("fork-bare")["summary"]
    image = bare.build_from([ANSWER], "problem_child_first", build_dir=tmp_path)
    fields = bare.run("fork", image=image, timeout=30).fields()

    assert fields.get("first_to_finish") == 1, "the parent still finished first"
    for claim in (
        "results_differ",
        "both_ran",
        "child_saw_the_parents_byte",
        "childs_write_stayed_in_its_own_page",
    ):
        assert fields.get(claim) == committed[claim], (
            f"{claim} changed — the reordering was supposed to leave the results alone"
        )


@pytest.mark.problem
def test_the_reader_said_what_must_be_saved():
    assert len(WHAT_HAS_TO_BE_SAVED.split()) >= 6, (
        "Problem 9.1: WHAT_HAS_TO_BE_SAVED wants a sentence"
    )
