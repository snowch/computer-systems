"""Checks Problem 6.2 by comparing the reader's prediction with their own run.

The right answer is never stored here: it comes out of the machine, and the test only insists
that the reader committed to a figure first and that the figure matched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from tests.one_page_table_two_harts.problem_2_no_identity import YOUR_PREDICTION

ANSWER = Path(__file__).parent / "answer_broken.c"


@pytest.mark.problem
def test_the_prediction_matched_the_machine(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 6.2: put your program in {ANSWER.name} beside this test"
    assert YOUR_PREDICTION >= 0, "Problem 6.2: YOUR_PREDICTION is still unset"

    image = bare.build_from([ANSWER], "problem_broken", build_dir=tmp_path)
    fields = bare.run("paging", image=image, timeout=30).fields()
    observed = fields.get("failure_cause")
    assert observed, "the program did not report a failure cause — did anything actually break?"
    assert observed == YOUR_PREDICTION, (
        f"you predicted {YOUR_PREDICTION}; the machine reported {observed}"
    )
