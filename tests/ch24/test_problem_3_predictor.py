"""Problem 17.3 — how many does a two-bit predictor get wrong?

Simulated by the test from the same rules the stub states, so the key is derived. The alternating
sequence is the one that matters: it is why two bits rather than one.
"""

from __future__ import annotations

import pytest

from tests.ch24.harness import ask

SEQUENCES = [
    "TTTTTTTT",
    "NNNNNNNN",
    "TNTNTNTN",
    "TTTTNNNN",
    "TTTNTTTN",
    "T",
    "NT",
]


def expected(outcomes: str) -> int:
    counter, wrong = 0, 0
    for outcome in outcomes:
        predicted_taken = counter >= 2
        taken = outcome == "T"
        if predicted_taken != taken:
            wrong += 1
        counter = min(3, counter + 1) if taken else max(0, counter - 1)
    return wrong


def one_bit(outcomes: str) -> int:
    state, wrong = False, 0
    for outcome in outcomes:
        taken = outcome == "T"
        if state != taken:
            wrong += 1
        state = taken
    return wrong


def test_two_bits_beat_one_on_the_alternating_pattern():
    """Scaffolding: the reason the predictor has two bits must be visible in the cases."""
    assert one_bit("TNTNTNTN") == 8, "a one-bit predictor gets every alternating branch wrong"
    assert expected("TNTNTNTN") < one_bit("TNTNTNTN"), "and two bits must do better"
    assert expected("TTTTTTTT") <= 2, "a settled predictor should be wrong at most while settling"


@pytest.mark.problem
def test_the_saturating_counter_is_simulated_correctly(predictor):
    answered = ask(predictor, [f"m{s}" for s in SEQUENCES])
    wrong = {
        s: {"expected": expected(s), "got": answered["mispredicts"][s]}
        for s in SEQUENCES
        if answered["mispredicts"][s] != expected(s)
    }
    assert not wrong, (
        "two bits, saturating, starting at strongly not-taken; states 0 and 1 predict not-taken: "
        f"{wrong}"
    )
