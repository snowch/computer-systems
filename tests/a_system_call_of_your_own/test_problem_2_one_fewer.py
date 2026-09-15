"""Checks Problem 7.2 by running the reader's program and watching the value fail to survive."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.a_system_call_of_your_own.problem_2_one_fewer import WHICH_REGISTER

ANSWER = Path(__file__).parent / "answer_fewer.c"


def test_the_chapters_frame_holds_thirty_one():
    """Scaffolding: the count the reader is reducing by one."""
    assert load_result("syscall-bare")["summary"]["registers_in_frame"] == 31


@pytest.mark.problem
def test_the_omission_is_visible(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 7.2: put your program in {ANSWER.name} beside this test"
    assert WHICH_REGISTER >= 1, "Problem 7.2: WHICH_REGISTER is still unset"
    assert WHICH_REGISTER != 2, (
        "x2 is the stack pointer and the stub handles it separately — pick another"
    )

    image = bare.build_from([ANSWER], "problem_fewer", build_dir=tmp_path)
    fields = bare.run("syscall", image=image, timeout=30).fields()
    assert fields.get("dropped_register") == WHICH_REGISTER, (
        "the program reports dropping a different register than the one you named"
    )
    assert fields["before"] != fields["after"], (
        "the value survived, so the register you dropped was not actually in use across the call"
    )
