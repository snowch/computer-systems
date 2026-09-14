"""Problem 14.2 — how many repetitions before the instrument stops dominating?

Every answer follows from the inequality in the stub, so the key is computed. The case worth
noticing is the one where the work is already far larger than the clock and the answer is one:
repeating cheap things is a technique, not a ritual.
"""

from __future__ import annotations

import math

import pytest

from tests.ch14.harness import ask

CASES = [(100, 20, 10), (100, 20, 100), (1, 20, 100), (10000, 20, 100), (0, 20, 10), (5, 5, 1)]


def expected(work: int, clock: int, budget: int) -> int:
    if work == 0:
        return 0
    return max(1, math.ceil(clock * budget / work))


def test_the_cases_include_both_ends():
    """Scaffolding: one repetition must sometimes be enough, and sometimes be nowhere near."""
    answers = [expected(*case) for case in CASES]
    assert 1 in answers and max(answers) > 100
    assert expected(0, 20, 10) == 0, "work of zero is a question without an answer"


@pytest.mark.problem
def test_the_count_shrinks_the_instrument_to_the_budget(measuring):
    answered = ask(measuring, [f"r{w},{c},{b}" for w, c, b in CASES])
    wrong = {
        f"work {w}, clock {c}, budget one in {b}": {
            "expected": expected(w, c, b),
            "got": answered["repetitions"][f"{w},{c},{b}"],
        }
        for w, c, b in CASES
        if answered["repetitions"][f"{w},{c},{b}"] != expected(w, c, b)
    }
    assert not wrong, f"the smallest n with clock * budget <= work * n: {wrong}"
