"""Problem 2.1 — allocation with nothing underneath it.

The scripts are chosen so the exhaustion case cannot be avoided: one of them asks for more entries
than the pool has, which is the case an application programmer has never had to write and the one
a kernel meets on a busy machine.
"""

from __future__ import annotations

import pytest

from tests.ch02.harness import POOL, ask

# `r` reset, `a` allocate, a digit frees that index, `x` frees an index outside the pool.
SCRIPTS = {
    "three in a row": "raaa",
    "fill it exactly": "r" + "a" * POOL,
    "ask for one too many": "r" + "a" * (POOL + 2),
    "free the middle and ask again": "raaaa1a",
    "free one that was never used": "raa5a",
    "free the same entry twice": "raaa0" + "0a",
    "free outside the pool": "raax" + "a",
    "reset puts them all back": "r" + "a" * POOL + "r" + "aa",
}


def expected(script: str) -> list[int]:
    used = [False] * POOL
    handed: list[int] = []
    for op in script:
        if op == "r":
            used = [False] * POOL
        elif op == "a":
            free = next((i for i, taken in enumerate(used) if not taken), -1)
            if free >= 0:
                used[free] = True
            handed.append(free)
        elif op.isdigit():
            index = int(op)
            if 0 <= index < POOL:
                used[index] = False
    return handed


def test_a_full_pool_reports_it_rather_than_growing():
    """Scaffolding: the answer to 'no entry left' is a value, not an exception and not a crash."""
    handed = expected(SCRIPTS["ask for one too many"])
    assert handed[:POOL] == list(range(POOL))
    assert handed[POOL:] == [-1, -1]


def test_freeing_makes_exactly_that_entry_available_again():
    """Scaffolding: the lowest-index rule, which is what makes this testable at all."""
    assert expected(SCRIPTS["free the middle and ask again"]) == [0, 1, 2, 3, 1]


def test_a_free_that_should_change_nothing_changes_nothing():
    """Scaffolding: three ways to be asked to free something that is not allocated.

    A kernel meets all three from buggy callers, and none of them may hand the same entry out
    twice — which is the failure that corrupts two processes at once.
    """
    assert expected(SCRIPTS["free one that was never used"]) == [0, 1, 2]
    assert expected(SCRIPTS["free the same entry twice"]) == [0, 1, 2, 0]
    assert expected(SCRIPTS["free outside the pool"]) == [0, 1, 2]


@pytest.mark.problem
def test_the_pool_hands_out_and_takes_back(runtime):
    names = sorted(SCRIPTS)
    answered = ask(runtime, [f"p{SCRIPTS[name]}" for name in names])
    wrong = {
        name: {"expected": expected(SCRIPTS[name]), "got": answered["pool"][i]}
        for i, name in enumerate(names)
        if answered["pool"][i] != expected(SCRIPTS[name])
    }
    assert not wrong, f"lowest unused index, -1 when there is none, and no double handout: {wrong}"
