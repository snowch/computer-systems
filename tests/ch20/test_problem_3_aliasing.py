"""Problem 20.3 — why a fixed sampling period produces a confident, repeatable, wrong answer.

The cases are chosen so that the answer ranges from the whole loop down to a single position, and
the scaffolding asserts the worst case explicitly: a period that divides the loop samples one
instruction, for ever, and nothing about the profile says so.
"""

from __future__ import annotations

import math

import pytest

from tests.ch20.harness import ask

# (sample period, loop period), both in cycles
CASES = {
    "coprime, so every position": (9_973, 512),
    "the period is a multiple of the loop": (4_096, 512),
    "a power of two against a power of two": (1_024, 768),
    "one cycle apart from a multiple": (4_097, 512),
    "the loop is longer than the period": (97, 10_000),
    "both odd and sharing a factor": (3_003, 1_001),
    "a single cycle": (1, 4_096),
}


def expected(sample_period: int, loop_period: int) -> int:
    return loop_period // math.gcd(sample_period, loop_period)


def test_a_period_that_divides_the_loop_sees_one_instruction():
    """Scaffolding: the worst case, which is the one the problem exists for."""
    assert expected(*CASES["the period is a multiple of the loop"]) == 1


def test_one_cycle_of_difference_recovers_the_whole_loop():
    """Scaffolding: the fix, and why profilers jitter the period rather than tune it.

    Between the two cases below nothing about the program changed. The sampling period moved by a
    cycle, and the profile went from one position to all of them.
    """
    assert (
        expected(*CASES["one cycle apart from a multiple"])
        == CASES["one cycle apart from a multiple"][1]
    )


def test_the_answer_never_exceeds_the_loop():
    """Scaffolding: a sanity bound that a plausible wrong formula fails."""
    assert all(expected(*case) <= case[1] for case in CASES.values())


@pytest.mark.problem
def test_the_positions_visited_are_decided_by_a_common_factor(profiler):
    names = sorted(CASES)
    answered = ask(profiler, [f"a{CASES[name][0]},{CASES[name][1]}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["aliased"][i]}
        for i, name in enumerate(names)
        if answered["aliased"][i] != expected(*CASES[name])
    }
    assert not wrong, (
        "sample i lands at (i * period) mod loop, and that sequence visits the multiples of one "
        f"number: {wrong}"
    )
