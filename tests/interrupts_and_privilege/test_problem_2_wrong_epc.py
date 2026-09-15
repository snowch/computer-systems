"""Checks Problem 5.2 by running the reader's program and comparing its two numbers.

The expected and actual figures both come out of the run, so the test never has to know what the
right answer was — only that the program produced a discrepancy and that it survived doing so.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from tests.interrupts_and_privilege.problem_2_wrong_epc import WHAT_GOES_WRONG

ANSWER = Path(__file__).parent / "answer_skip.c"


@pytest.mark.problem
def test_the_damage_is_visible_and_is_not_a_crash(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 5.2: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_skip", build_dir=tmp_path)
    # Reaching the end at all is half the point: the program has to survive the damage.
    fields = bare.run("privilege", image=image, timeout=30).fields()

    assert "expected" in fields and "actual" in fields, "the program did not print both figures"
    assert fields["actual"] != fields["expected"], (
        "the two agree, so nothing was lost — the advance did not do what the problem is about"
    )


@pytest.mark.problem
def test_the_reader_described_the_damage():
    assert len(WHAT_GOES_WRONG.split()) >= 8, "Problem 5.2: WHAT_GOES_WRONG wants a sentence"
