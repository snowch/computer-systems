"""Problem 21.1 — the tail, and where vectorising stops being worth the code.

The cases run from a loop long enough for the tail to disappear down to one shorter than the
vector, where widening buys exactly nothing and the compiler has emitted a great deal of code to
achieve it.
"""

from __future__ import annotations

import pytest

from tests.ch28.harness import ask

# (elements, lanes)
CASES = {
    "long, and a multiple of the width": (1_000_000, 4),
    "long, and not a multiple": (1_000_001, 4),
    "shorter than the vector": (3, 4),
    "exactly one vector": (4, 4),
    "one element past a vector": (5, 4),
    "sixteen lanes over a short loop": (20, 16),
    "a single lane": (1_000, 1),
    "one element": (1, 8),
}


def expected(n: int, lanes: int) -> int:
    return 100 * n // (n // lanes + n % lanes)


def test_a_loop_shorter_than_the_vector_gains_nothing():
    """Scaffolding: the case worth knowing, and the one a lane count alone hides."""
    assert expected(*CASES["shorter than the vector"]) == 100
    assert expected(*CASES["one element"]) == 100


def test_a_long_loop_reaches_the_lane_count_and_never_passes_it():
    """Scaffolding: the bound, from the other side."""
    assert expected(*CASES["long, and a multiple of the width"]) == 400
    assert expected(*CASES["long, and not a multiple"]) < 400
    assert all(expected(n, lanes) <= 100 * lanes for n, lanes in CASES.values())


def test_one_element_past_a_vector_is_worse_than_the_vector_itself():
    """Scaffolding: the tail is charged whole, so the curve is a sawtooth, not a slope."""
    assert expected(*CASES["one element past a vector"]) < expected(*CASES["exactly one vector"])


@pytest.mark.problem
def test_the_speedup_is_the_elements_over_the_iterations(lanes):
    names = sorted(CASES)
    answered = ask(lanes, [f"w{CASES[name][0]},{CASES[name][1]}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["speedup"][i]}
        for i, name in enumerate(names)
        if answered["speedup"][i] != expected(*CASES[name])
    }
    assert not wrong, f"full vectors plus a scalar element each for the remainder: {wrong}"
