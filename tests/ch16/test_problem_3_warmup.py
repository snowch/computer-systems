"""Problem 14.3 — how many leading samples are warm-up?

Derived from the sample sequences, which are written to separate warm-up from interference: one
has a slow start, one has a slow sample in the middle and no warm-up at all, and one has both.
"""

from __future__ import annotations

import pytest

from tests.ch16.harness import ask

TOLERANCE = 10

SEQUENCES = [
    [100, 100, 100],
    [500, 300, 100, 100, 104],
    [100, 100, 500, 100],
    [900, 100, 100, 500, 100],
    [500, 400, 300],
]


def expected(samples: list[int], tolerance: int) -> int:
    for k in range(len(samples)):
        tail = samples[k:]
        floor = min(tail)
        band = floor * (100 + tolerance)
        settled = all(v * 100 <= band for v in tail)
        discarded_were_slow = all(v * 100 > band for v in samples[:k])
        if settled and discarded_were_slow:
            return k
    return len(samples)


def test_warmup_and_interference_are_separated_by_the_cases():
    """Scaffolding: a spike in the middle is not warm-up and must not be trimmed away."""
    assert expected([100, 100, 500, 100], TOLERANCE) == len([100, 100, 500, 100]), (
        "a mid-run spike cannot be removed by discarding a prefix, so no prefix qualifies"
    )
    assert expected([500, 300, 100, 100, 104], TOLERANCE) == 2, "a slow start is warm-up"
    assert expected([100, 100, 100], TOLERANCE) == 0, "an already-warm set discards nothing"


@pytest.mark.problem
def test_only_a_leading_run_of_slow_samples_is_warmup(measuring):
    commands = [f"w{i},{TOLERANCE},{'.'.join(str(v) for v in s)}" for i, s in enumerate(SEQUENCES)]
    answered = ask(measuring, commands)
    wrong = {
        str(s): {"expected": expected(s, TOLERANCE), "got": answered["warmup"][i]}
        for i, s in enumerate(SEQUENCES)
        if answered["warmup"][i] != expected(s, TOLERANCE)
    }
    assert not wrong, (
        "warm-up is a property of position: the smallest prefix whose removal leaves every "
        f"remaining sample within tolerance of the rest: {wrong}"
    )
