"""Problem 10.2 — which reorderings does each kind of barrier actually prevent?

The four cases that matter are the two where the annotation is on the operation it does not help:
an acquire on the second operation, and a release on the first. Both are ordinary mistakes and
both leave the pair free to be reordered.
"""

from __future__ import annotations

import pytest

from tests.ch12.harness import ask

#: (first, second, barrier, same address) -> may the machine make them visible in the opposite
#: order?
CASES = {
    ("w", "w", "n", 0): 1,
    ("r", "w", "n", 0): 1,
    ("w", "r", "n", 0): 1,
    ("w", "w", "f", 0): 0,
    ("r", "r", "f", 0): 0,
    # The first carries acquire: later work cannot move before it.
    ("w", "w", "a", 0): 0,
    ("r", "w", "a", 0): 0,
    # The second carries acquire: that says nothing about work already behind it.
    ("w", "w", "A", 0): 1,
    ("r", "w", "A", 0): 1,
    # The second carries release: earlier work cannot move after it.
    ("w", "w", "l", 0): 0,
    ("w", "r", "l", 0): 0,
    # The first carries release: that says nothing about work still ahead of it.
    ("w", "w", "L", 0): 1,
    ("w", "r", "L", 0): 1,
    # Same location: never reordered, whatever else is or is not present.
    ("w", "w", "n", 1): 0,
    ("r", "w", "n", 1): 0,
    ("w", "r", "n", 1): 0,
    ("w", "w", "A", 1): 0,
    ("w", "r", "L", 1): 0,
}


def test_the_asymmetry_is_actually_asked_about():
    """Scaffolding: every parameter has to change an answer, or it is not being asked about."""
    assert CASES[("w", "w", "a", 0)] != CASES[("w", "w", "A", 0)], "acquire is one-way or nothing"
    assert CASES[("w", "w", "l", 0)] != CASES[("w", "w", "L", 0)], "and so is release"
    assert CASES[("w", "w", "n", 0)] != CASES[("w", "w", "n", 1)], "same location settles it alone"
    assert CASES[("w", "w", "n", 0)] == 1 and CASES[("w", "w", "f", 0)] == 0


@pytest.mark.problem
def test_each_barrier_prevents_only_what_it_promises(locking):
    commands = [f"r{first}{second}{barrier}{same}" for first, second, barrier, same in CASES]
    answered = ask(locking, commands)
    wrong = {
        f"{first} then {second}, barrier {barrier!r}{', same address' if same else ''}": {
            "expected": "may reorder" if expected else "may not",
            "got": "may reorder" if answered["reorder"][key] else "may not",
        }
        for case, expected in CASES.items()
        for first, second, barrier, same in [case]
        for key in [f"{first}{second}{barrier}{same}"]
        if answered["reorder"][key] != expected
    }
    assert not wrong, (
        "an acquire stops later work moving earlier and nothing else; a release stops earlier "
        f"work moving later and nothing else: {wrong}"
    )
