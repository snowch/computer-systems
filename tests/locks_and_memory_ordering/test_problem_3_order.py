"""Problem 10.3 — do these two paths disagree about the order locks are taken in?

Every answer follows from the two strings, so nothing is stored. The cases include the two that
look alike and are not: paths that share every lock and agree, and paths that share only two and
do not.
"""

from __future__ import annotations

import pytest

from tests.locks_and_memory_ordering.harness import ask

CASES = {
    ("AB", "BA"): 1,
    ("AB", "AB"): 0,
    ("ABC", "ABC"): 0,
    ("ABC", "CBA"): 1,
    ("ABC", "BA"): 1,
    ("AB", "BC"): 0,
    ("AB", "CD"): 0,
    ("A", "A"): 0,
    ("A", "AB"): 0,
    ("ABCD", "ADCB"): 1,
}


def test_the_cases_separate_sharing_from_disagreeing():
    """Scaffolding: using the same locks is not the question, and using few is not safety."""
    assert CASES[("ABC", "ABC")] == 0, "sharing every lock in the same order is safe"
    assert CASES[("AB", "BA")] == 1, "sharing two locks in opposite orders is not"
    assert CASES[("AB", "BC")] == 0, "and an overlap that agrees about the overlap is fine"


@pytest.mark.problem
def test_only_a_pair_taken_both_ways_is_a_conflict(locking):
    commands = [f"d{first},{second}" for first, second in CASES]
    answered = ask(locking, commands)
    wrong = {
        f"{first} against {second}": {
            "expected": expected,
            "got": answered["conflict"][(first, second)],
        }
        for (first, second), expected in CASES.items()
        if answered["conflict"][(first, second)] != expected
    }
    assert not wrong, (
        "a conflict is a pair of locks the two paths take in opposite orders, and nothing "
        f"else: {wrong}"
    )
