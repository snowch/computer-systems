"""Checks Problem 7.3 by running the reader's program; the register name is checked by using it."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from tests.a_system_call_of_your_own.problem_3_whose_stack import (
    THE_REGISTER_FOR_THIS,
    WHAT_A_BAD_STACK_POINTER_DOES,
)

ANSWER = Path(__file__).parent / "answer_stack.c"


@pytest.mark.problem
def test_the_frame_moved_and_the_call_still_works(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 7.3: put your program in {ANSWER.name} beside this test"

    source = ANSWER.read_text()
    assert THE_REGISTER_FOR_THIS.strip(), "Problem 7.3: THE_REGISTER_FOR_THIS is still empty"
    assert THE_REGISTER_FOR_THIS.strip().lower() in source.lower(), (
        "you named a register but your program does not use it"
    )

    image = bare.build_from([ANSWER], "problem_stack", build_dir=tmp_path)
    fields = bare.run("syscall", image=image, timeout=30).fields()
    assert fields.get("frame_on_callers_stack") == 0, "the frame is still on the caller's stack"
    assert fields.get("result_returned") == 7, "the call stopped working"


@pytest.mark.problem
def test_the_reader_said_what_goes_wrong():
    assert len(WHAT_A_BAD_STACK_POINTER_DOES.split()) >= 8, (
        "Problem 7.3: WHAT_A_BAD_STACK_POINTER_DOES wants a sentence"
    )
