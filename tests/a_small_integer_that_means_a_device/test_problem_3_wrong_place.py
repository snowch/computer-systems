"""Checks Problem 8.3 against ch08's own committed figure, so the regression is measured."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.a_small_integer_that_means_a_device.problem_3_wrong_place import WHAT_BREAKS

ANSWER = Path(__file__).parent / "answer_cursor.c"


@pytest.mark.problem
def test_the_sharing_really_stops(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 8.3: put your program in {ANSWER.name} beside this test"

    correct = load_result("descriptors-bare")["summary"]["shared_cursor"]
    image = bare.build_from([ANSWER], "problem_cursor", build_dir=tmp_path)
    fields = bare.run("descriptors", image=image, timeout=30).fields()

    assert "shared_cursor" in fields, "the program did not report a cursor"
    assert fields["shared_cursor"] != correct, (
        "the cursor still ends where ch08's does, so the two descriptors are still sharing one"
    )
    assert fields.get("dup_shares_the_open_file") == 0, (
        "the program still claims the duplicate shares an open file"
    )


@pytest.mark.problem
def test_the_reader_named_what_breaks():
    assert len(WHAT_BREAKS.split()) >= 6, "Problem 8.3: WHAT_BREAKS wants a sentence"
