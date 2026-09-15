"""Checks Problem 9.2 by running the reader's program: a failure that is not a successful fork."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from tests.fork_built_rather_than_read.problem_2_full_table import WHY_NOT_ZERO

ANSWER = Path(__file__).parent / "answer_full.c"


@pytest.mark.problem
def test_the_table_filled_and_the_machine_survived(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 9.2: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_full", build_dir=tmp_path)
    fields = bare.run("fork", image=image, timeout=30).fields()

    assert fields.get("successful_forks", 0) >= 1, "nothing ever succeeded"
    assert fields.get("caller_survived") == 1, "the caller did not get to handle the failure"
    assert "failed_fork_result" in fields, "the failing call reported nothing"
    assert fields["failed_fork_result"] != fields["successful_forks"], (
        "the failure is indistinguishable from a successful fork returning a child id"
    )


@pytest.mark.problem
def test_the_reader_ruled_out_zero():
    assert len(WHY_NOT_ZERO.split()) >= 5, "Problem 9.2: WHY_NOT_ZERO wants a phrase"
