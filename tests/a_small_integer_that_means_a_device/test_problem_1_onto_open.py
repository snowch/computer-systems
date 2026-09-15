"""Checks Problem 8.1 by running the reader's program: consistent, and not a blanket refusal."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.a_small_integer_that_means_a_device.problem_1_onto_open import YOUR_CHOICE_AND_WHY

ANSWER = Path(__file__).parent / "answer_onto.c"
BAD = (1 << 64) - 1


def test_the_chapters_dup_returned_its_target():
    """Scaffolding: the behaviour being refined."""
    assert load_result("descriptors-bare")["summary"]["dup_returned"] == 3


@pytest.mark.problem
def test_the_choice_is_consistent_and_not_a_blanket_refusal(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 8.1: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_onto", build_dir=tmp_path)
    fields = bare.run("descriptors", image=image, timeout=30).fields()
    assert fields.get("dup_onto_free") not in (None, BAD), (
        "duplicating onto a free slot must still work — this refuses everything"
    )
    assert "dup_onto_open" in fields and "old_file_still_reachable" in fields


@pytest.mark.problem
def test_the_reader_justified_it():
    assert len(YOUR_CHOICE_AND_WHY.split()) >= 10, (
        "Problem 8.1: YOUR_CHOICE_AND_WHY wants a sentence with a reason in it"
    )
