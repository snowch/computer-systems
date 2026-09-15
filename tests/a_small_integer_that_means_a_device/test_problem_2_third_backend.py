"""Checks Problem 8.2: three destinations, one caller, and the discard really discards."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare

ANSWER = Path(__file__).parent / "answer_third.c"


@pytest.mark.problem
def test_three_backends_one_caller(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 8.2: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_third", build_dir=tmp_path)
    fields = bare.run("descriptors", image=image, timeout=30).fields()
    assert fields.get("backends") == 3
    written = {fields.get(k) for k in ("wrote_to_console", "wrote_to_memory", "wrote_to_discard")}
    assert None not in written, "all three destinations must report what they accepted"
    assert len(written) == 1, (
        "the three calls accepted different byte counts, so the caller is not identical across "
        "them — a discard should accept everything, like the others"
    )
    assert fields.get("read_from_discard") == 0, "the discard gave something back"
