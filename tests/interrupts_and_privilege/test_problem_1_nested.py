"""Checks Problem 5.1 by building and booting the reader's program.

The nesting is measured, not asserted, and no part of the answer is stored here: a reader who
gets there by a different route than the one the chapter hints at still passes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.interrupts_and_privilege.problem_1_nested import WHAT_STOPS_IT_BY_DEFAULT

ANSWER = Path(__file__).parent / "answer_nested.c"


def test_the_chapters_interrupt_really_arrived():
    """Scaffolding: there is an interrupt to nest inside."""
    summary = load_result("privilege-bare")["summary"]
    assert summary["interrupt_arrived"] == 1
    assert summary["cause_is_asynchronous"] == 1


@pytest.mark.problem
def test_the_readers_handler_was_interrupted(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 5.1: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_nested", build_dir=tmp_path)
    fields = bare.run("privilege", image=image, timeout=30).fields()
    assert fields.get("handler_entries", 0) >= 2, (
        "the handler ran fewer than twice, so nothing nested"
    )
    assert fields.get("nested") == 1, (
        "the handler ran more than once, but never while it was already running — two interrupts "
        "one after the other is not the same thing"
    )


@pytest.mark.problem
def test_the_reader_explained_the_default():
    assert len(WHAT_STOPS_IT_BY_DEFAULT.split()) >= 6, (
        "Problem 5.1: WHAT_STOPS_IT_BY_DEFAULT wants a sentence"
    )
