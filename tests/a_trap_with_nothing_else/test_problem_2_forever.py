"""Checks Problem 4.2 by running what the reader wrote and watching it fail to finish.

Nothing about the answer is stored. The loop is demonstrated rather than asserted: the harness
gives up on a program that does not stop, and that giving up is the check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.a_trap_with_nothing_else.problem_2_forever import (
    THE_INSTRUCTION_THAT_REPEATS,
    WHY_NO_ERROR,
)

ANSWER = Path(__file__).parent / "answer_forever.c"


def test_the_working_program_stops_on_its_own():
    """Scaffolding: the thing being contrasted against really does finish."""
    assert load_result("trap-bare")["summary"]["taken"] == 1


@pytest.mark.problem
def test_the_readers_program_never_finishes(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 4.2: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_forever", build_dir=tmp_path)
    with pytest.raises(RuntimeError) as raised:
        bare.run("trap", image=image, timeout=15)
    assert "looping" in str(raised.value), (
        "the program stopped, so it is not looping — check you removed the advance rather than "
        "the trap"
    )


@pytest.mark.problem
def test_the_reader_named_the_instruction_and_explained_the_silence():
    assert THE_INSTRUCTION_THAT_REPEATS.strip(), (
        "Problem 4.2: THE_INSTRUCTION_THAT_REPEATS is still empty"
    )
    assert THE_INSTRUCTION_THAT_REPEATS.strip().lower() not in {"loop", "handler", "trap"}, (
        "name the instruction, not what it does"
    )
    assert len(WHY_NO_ERROR.split()) >= 8, "Problem 4.2: WHY_NO_ERROR wants a sentence"
