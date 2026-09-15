"""Problem 7.3 — say where the walk stopped, which is what a fault actually tells you.

Every expected answer here follows from how the test built the address space rather than from a
stored constant: a probe in an untouched gigabyte can only fail at the top level, one in a mapped
gigabyte but an untouched two-megabyte region can only fail in the middle, and one beside a
mapped page can only fail at the bottom.
"""

from __future__ import annotations

import pytest

from tests.virtual_memory.harness import ask, maps, run_of

GIB = 1 << 30
TWO_MIB = 1 << 21

MAPPED = run_of(0x0, 4, 0x2A000)

#: probe -> the level whose table has no valid entry for it, by construction.
CASES = {
    0x3000: -1,  # the fourth page mapped above: found, so nothing is missing
    0x8000: 0,  # same two-megabyte region, so only the last table is short
    TWO_MIB: 1,  # same gigabyte, different two megabytes: the middle table is short
    GIB: 2,  # a gigabyte nothing has ever touched: the root is short
}


def test_the_cases_are_three_different_failures_and_one_success(walk):
    """Scaffolding: the problem is not answerable by returning a constant."""
    assert sorted(set(CASES.values())) == [-1, 0, 1, 2]
    assert 0x3000 in {va for va, _ in MAPPED}, "the mapped probe must be one of the mapped pages"


@pytest.mark.problem
def test_the_walk_reports_where_it_stopped(walk):
    """All four cases in one test, deliberately.

    Split into four, a stub that returns any constant passes one of them, and a green tick beside
    an unsolved problem is worse than no tick at all.
    """
    answered = ask(walk, maps(MAPPED) + [f"f{probe:#x}" for probe in sorted(CASES)])
    wrong = {
        f"{probe:#x}": {"expected": expected, "reported": answered["missing"][probe]}
        for probe, expected in CASES.items()
        if answered["missing"][probe] != expected
    }
    assert not wrong, (
        "the walk stops at a different level from the one these addresses force. Level -1 means "
        f"the address is mapped; 2, 1 and 0 name the table that had no valid entry: {wrong}"
    )
