"""Checks Problem 1.1. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.reading_a_listing.problem_1_lengths import instruction_lengths

#: (description, addresses, end, lengths). Taken from the shape of real RV64GC and AArch64 output.
CASES = [
    ("every instruction the same width", [0, 4, 8], 12, [4, 4, 4]),
    ("the chapter's own two-instruction function", [0, 4], 6, [4, 2]),
    ("compressed forms mixed in", [0, 2, 6, 8, 12], 14, [2, 4, 2, 4, 2]),
    ("one instruction, and the function ends", [0], 4, [4]),
    ("a function that is entirely compressed", [0, 2, 4], 6, [2, 2, 2]),
]


def test_the_cases_contain_both_widths():
    """Scaffolding: a table where every instruction were four bytes would test nothing."""
    widths = {n for _, _, _, lengths in CASES for n in lengths}
    assert widths == {2, 4}, f"the table must exercise both widths, got {widths}"


def test_the_last_instruction_needs_the_end():
    """Scaffolding: the final length cannot come from the addresses alone, which is the point."""
    assert CASES[1][3][-1] != CASES[0][3][-1], (
        "two cases must end on instructions of different lengths, or `end` is never needed"
    )


@pytest.mark.problem
@pytest.mark.parametrize(
    ("description", "addresses", "end", "expected"), CASES, ids=[c[0] for c in CASES]
)
def test_each_instruction_is_as_long_as_the_gap(description, addresses, end, expected):
    try:
        answer = instruction_lengths(list(addresses), end)
    except NotImplementedError:
        pytest.fail("Problem 1.1 is not solved — see tests/reading_a_listing/problem_1_lengths.py")
    assert answer == expected, (
        f"{description}: an instruction is as long as the distance to the next address, and the "
        f"last one reaches `end`. You said {answer}, the listing says {expected}"
    )
