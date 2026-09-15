"""Checks Problem 7.1 by running the reader's program and comparing its two outcomes."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.a_system_call_of_your_own.problem_1_add_a_call import WHY_THE_SENTINEL_IS_SAFE

ANSWER = Path(__file__).parent / "answer_call.c"


def test_the_chapter_already_refuses_an_unknown_number():
    """Scaffolding: the failure mode the reader must not simply reuse."""
    assert load_result("syscall-bare")["summary"]["unknown_call_refused"] == 1


@pytest.mark.problem
def test_success_and_failure_are_distinguishable(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 7.1: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_call", build_dir=tmp_path)
    fields = bare.run("syscall", image=image, timeout=30).fields()
    assert "ok_result" in fields and "failed_result" in fields, "both outcomes must be reported"
    assert fields["ok_result"] != fields["failed_result"], (
        "the call returns the same thing whether it worked or not, so the caller cannot tell"
    )
    assert fields.get("caller_can_tell") == 1


@pytest.mark.problem
def test_the_reader_justified_the_sentinel():
    assert len(WHY_THE_SENTINEL_IS_SAFE.split()) >= 8, (
        "Problem 7.1: WHY_THE_SENTINEL_IS_SAFE wants a sentence"
    )
