"""Checks Problem 9.3 by making the reader produce the fault rather than describe it.

The cause code is never stored here. It comes out of the reader's own run, and the test only
insists that a fault happened, that it happened on a write, and that the page stayed readable —
which is what makes it the copy-on-write case rather than simply an unmapped page.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from tests.fork_built_rather_than_read.problem_3_lazy import (
    THE_BIT_YOU_CLEARED,
    WHAT_IT_WOULD_REMOVE,
)

ANSWER = Path(__file__).parent / "answer_lazy.c"


@pytest.mark.problem
def test_the_write_faulted_while_the_page_stayed_readable(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 9.3: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_lazy", build_dir=tmp_path)
    fields = bare.run("fork", image=image, timeout=30).fields()

    assert fields.get("write_fault_cause", 0) > 0, (
        "no fault was reported — the write succeeded, so the page was still writable"
    )
    assert fields.get("page_was_readable") == 1, (
        "the page was not readable either, so this is an unmapped page rather than the "
        "copy-on-write case"
    )


@pytest.mark.problem
def test_the_reader_named_the_bit_and_the_saving():
    assert THE_BIT_YOU_CLEARED.strip().upper() in {"R", "W", "X", "U"}, (
        "Problem 9.3: name the bit by its letter"
    )
    assert len(WHAT_IT_WOULD_REMOVE.split()) >= 6, (
        "Problem 9.3: WHAT_IT_WOULD_REMOVE wants a sentence"
    )
