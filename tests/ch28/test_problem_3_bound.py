"""Problem 21.3 — the speedup as a fraction of the one the width allowed.

The scaffolding asserts the two readings the chapter cares about: a result near the bound means
the width was the constraint, and a result over it means something else changed and the comparison
is no longer between two versions of one loop.
"""

from __future__ import annotations

import pytest

from tests.ch28.harness import ask

# (scalar ns, vector ns, lanes)
CASES = {
    "the whole bound": (4_000, 1_000, 4),
    "most of it": (4_000, 1_300, 4),
    "half of it": (4_000, 2_000, 4),
    "none of it": (4_000, 4_000, 4),
    "over the bound": (4_000, 800, 4),
    "sixteen lanes, poorly used": (16_000, 4_000, 16),
    "two lanes, well used": (2_000, 1_050, 2),
}


def expected(scalar_ns: int, vector_ns: int, lanes: int) -> int:
    return 100 * scalar_ns // (vector_ns * lanes)


def test_the_bound_reached_exactly_is_a_hundred():
    """Scaffolding: the scale has to mean what the chapter says it means."""
    assert expected(*CASES["the whole bound"]) == 100
    assert expected(*CASES["none of it"]) == 25


def test_a_result_over_the_bound_is_reported_rather_than_clamped():
    """Scaffolding: clamping would hide the one answer that says the measurement is wrong.

    Beating the arithmetic bound means the vector version changed something else as well — the
    access pattern, the tail, the amount of work — and a number quietly pinned to a hundred would
    turn that finding into a success.
    """
    assert expected(*CASES["over the bound"]) > 100


def test_a_large_speedup_can_be_a_small_fraction_of_the_bound():
    """Scaffolding: the reason the chapter asks for this number instead of a speedup."""
    scalar, vector, width = CASES["sixteen lanes, poorly used"]
    assert scalar // vector == 4, "four times faster, which sounds good"
    assert expected(scalar, vector, width) == 25, "and a quarter of what the width allowed"


@pytest.mark.problem
def test_the_fraction_is_the_speedup_over_the_lane_count(lanes):
    names = sorted(CASES)
    answered = ask(lanes, [f"b{','.join(str(v) for v in CASES[name])}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["bound"][i]}
        for i, name in enumerate(names)
        if answered["bound"][i] != expected(*CASES[name])
    }
    assert not wrong, f"the measured speedup divided by the width, as a percentage: {wrong}"
