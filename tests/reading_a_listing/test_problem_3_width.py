"""Checks Problem 1.3. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.reading_a_listing.problem_3_width import element_width

#: (description, offset the instruction carries, elements the source stepped, element width)
CASES = [
    ("lw a0,4(a0) from p + 1", 4, 1, 4),
    ("ld a0,8(a0) from p + 1", 8, 1, 8),
    ("a byte pointer stepped once", 1, 1, 1),
    ("an int stepped three times", 12, 3, 4),
    ("a long stepped twice", 16, 2, 8),
    ("a short stepped five times", 10, 5, 2),
]


def test_the_two_listings_from_the_next_chapter_disagree():
    """Scaffolding: identical source, different width — the reason the problem exists."""
    narrow = next(c for c in CASES if c[0].startswith("lw"))
    wide = next(c for c in CASES if c[0].startswith("ld"))
    assert narrow[2] == wide[2], "both must step the same number of elements"
    assert narrow[3] != wide[3], "and must not come out the same width"


def test_the_offset_alone_is_not_the_answer():
    """Scaffolding: at least one case must step more than once, or width is just the offset."""
    assert any(steps > 1 for _, _, steps, _ in CASES)


@pytest.mark.problem
@pytest.mark.parametrize(
    ("description", "offset", "steps", "expected"), CASES, ids=[c[0] for c in CASES]
)
def test_the_offset_is_the_width_times_the_steps(description, offset, steps, expected):
    try:
        answer = element_width(offset, steps)
    except NotImplementedError:
        pytest.fail("Problem 1.3 is not solved — see tests/reading_a_listing/problem_3_width.py")
    assert answer == expected, (
        f"{description}: the compiler multiplied the width by the steps to get {offset}. "
        f"You said {answer}, it was {expected}"
    )
