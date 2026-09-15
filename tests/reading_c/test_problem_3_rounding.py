"""Problem 1.3 — rounding an address, which is arithmetic on a number and not on a pointer.

The cases include every boundary the kernel's own allocator crosses: an address already aligned,
one byte either side of one, and zero.
"""

from __future__ import annotations

import pytest

from tests.reading_c.harness import ask

PAGE = 4096
CASES = [
    (0, PAGE),
    (1, PAGE),
    (PAGE - 1, PAGE),
    (PAGE, PAGE),
    (PAGE + 1, PAGE),
    (0x80000000, PAGE),
    (0x80000001, PAGE),
    (0x8000_0FFF, PAGE),
    (12, 8),
    (16, 8),
    (0, 1),
    (0x3FFF_FFFF_FFFF, PAGE),
]


def expected(address: int, align: int) -> tuple[int, int]:
    down = address & ~(align - 1)
    return down, down if down == address else down + align


def test_an_aligned_address_is_its_own_answer_both_ways():
    """Scaffolding: the case a rounding-up expression written with a bare addition gets wrong."""
    for align in (1, 8, PAGE):
        for multiple in (0, align, align * 7):
            assert expected(multiple, align) == (multiple, multiple)


def test_rounding_up_and_down_differ_by_exactly_one_boundary():
    """Scaffolding: off a boundary, the two answers are one alignment apart and never more."""
    for address, align in CASES:
        down, up = expected(address, align)
        assert up - down in (0, align)
        assert down <= address <= up


@pytest.mark.problem
def test_both_directions_land_on_a_boundary(declarations):
    answered = ask(declarations, [f"r{address},{align}" for address, align in CASES])
    wrong = {
        f"{address:#x} to {align}": {
            "expected": expected(address, align),
            "got": answered["round"][i],
        }
        for i, (address, align) in enumerate(CASES)
        if answered["round"][i] != expected(address, align)
    }
    assert not wrong, (
        f"align is a power of two, so neither direction needs a division or a branch: {wrong}"
    )
