"""Checks Problem 2.3 by running the broken function and comparing it with honest arithmetic."""

from __future__ import annotations

import pytest

from tests.ch05.problem_3_break_it import COUNTER_EXAMPLE, UNSIGNED_BITS

LIMIT = 1 << UNSIGNED_BITS


def fits_as_written(start: int, length: int, size: int) -> bool:
    """The function exactly as chapter 2 prints it, wrapping the way `unsigned` wraps."""
    return ((start + length) % LIMIT) <= size


def fits_truthfully(start: int, length: int, size: int) -> bool:
    """The same question asked in a width that cannot overflow."""
    return start + length <= size


@pytest.mark.problem
def test_the_counter_example_is_in_range():
    assert COUNTER_EXAMPLE is not None, "Problem 2.3: COUNTER_EXAMPLE is still None"
    assert all(0 <= value < LIMIT for value in COUNTER_EXAMPLE), (
        f"all three values must fit in {UNSIGNED_BITS} bits — the bug needs no help from you"
    )


@pytest.mark.problem
def test_the_function_is_wrong_about_it():
    assert COUNTER_EXAMPLE is not None, "Problem 2.3: COUNTER_EXAMPLE is still None"
    start, length, size = COUNTER_EXAMPLE
    assert fits_as_written(start, length, size), (
        "the function has to answer *yes* for your triple — an input it correctly rejects is not "
        "a counter-example"
    )
    assert not fits_truthfully(start, length, size), (
        f"{start} + {length} really is within {size}, so the function was right"
    )


def test_the_two_functions_agree_almost_everywhere():
    """Scaffolding: the bug is rare, which is exactly why it survives code review.

    If these disagreed often the problem would be trivial and the function would never have been
    written. A spread of ordinary values must show no disagreement at all.
    """
    ordinary = [(0, 0, 0), (0, 10, 10), (5, 5, 100), (LIMIT - 1, 0, LIMIT - 1), (1, 1, 1)]
    for case in ordinary:
        assert fits_as_written(*case) == fits_truthfully(*case), case
