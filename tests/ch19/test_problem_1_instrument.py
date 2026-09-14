"""Problem 19.1 — where the clock goes, and what that does to the answer.

The key is arithmetic the test does itself, so nothing is stored. What makes the problem worth
setting is the pair of cases with identical costs and different placements: one reports the call,
the other reports the call plus the instrument, and neither looks wrong on its own.
"""

from __future__ import annotations

import pytest

from tests.ch19.harness import ask

# (call_ns, clock_ns, iterations, inside)
CASES = {
    "a cheap call, clock inside": (40, 25, 100_000, 1),
    "a cheap call, clock outside": (40, 25, 100_000, 0),
    "an expensive call, clock inside": (5_000, 25, 100_000, 1),
    "an expensive call, clock outside": (5_000, 25, 100_000, 0),
    "one iteration, clock outside": (40, 25, 1, 0),
    "one iteration, clock inside": (40, 25, 1, 1),
    "a free clock": (40, 0, 1_000, 1),
    "an instrument larger than the thing": (12, 60, 10_000, 1),
    "the same, amortised": (12, 60, 10_000, 0),
}


def expected(call_ns: int, clock_ns: int, iterations: int, inside: int) -> int:
    if inside:
        return call_ns + clock_ns
    return (iterations * call_ns + clock_ns) // iterations


def test_the_instrument_is_charged_per_call_or_charged_once():
    """Scaffolding: the whole problem is which of those two it is."""
    inside = expected(*CASES["a cheap call, clock inside"])
    outside = expected(*CASES["a cheap call, clock outside"])
    assert inside - 40 == 25, "inside the loop, every call carries the whole clock"
    assert outside == 40, "outside it, one clock read is divided by a hundred thousand"

    small = expected(*CASES["an instrument larger than the thing"])
    assert small > 5 * 12, "an instrument larger than the thing mostly measures the instrument"
    assert expected(*CASES["the same, amortised"]) == 12


def test_at_one_iteration_the_two_placements_agree():
    """Scaffolding, and the reason this is arithmetic rather than a rule.

    Putting the clock outside is not a trick that removes the overhead; it divides it. With
    nothing to divide by, the two forms are the same expression and must return the same number.
    """
    assert expected(*CASES["one iteration, clock outside"]) == expected(
        *CASES["one iteration, clock inside"]
    )


@pytest.mark.problem
def test_the_reported_cost_follows_the_clock(oscost):
    names = sorted(CASES)
    answered = ask(oscost, [f"r{','.join(str(n) for n in CASES[name])}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["reported"][i]}
        for i, name in enumerate(names)
        if answered["reported"][i] != expected(*CASES[name])
    }
    assert not wrong, (
        "a clock read inside the loop is added to every call; one outside it is divided by all "
        f"of them: {wrong}"
    )
