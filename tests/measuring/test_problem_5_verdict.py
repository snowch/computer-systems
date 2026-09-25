"""Problem 24.5 — the two kinds of "cannot tell".

Both comparisons below decline to name a winner and they mean opposite things. The samples are
built so that the situation is known by construction rather than stored as an answer: one pair is
drawn from the same floor, the other from floors that genuinely differ by less than the threshold.
"""

from __future__ import annotations

import random

import pytest

from bench.distribution import decide
from tests.measuring.judging import why_undecided

THRESHOLD = 0.05


def draw(rng: random.Random, floor: float, n: int) -> list[float]:
    """A benchmark-shaped sample set: a hard floor plus a one-sided tail."""
    return [floor + rng.expovariate(1 / (floor * 0.04)) for _ in range(n)]


def pair(same: bool, n: int = 300) -> dict:
    rng = random.Random(11)
    baseline = draw(rng, 1000.0, n)
    # Same floor, or one 2% below it — under the 5% threshold either way.
    candidate = draw(rng, 1000.0 if same else 980.0, n)
    return decide(baseline, candidate, threshold=THRESHOLD)


@pytest.mark.problem
def test_no_evidence_is_told_apart_from_too_small_to_matter():
    identical = pair(same=True)
    real_but_tiny = pair(same=False)

    # The premise of the problem: both decline, for different reasons.
    assert identical["verdict"] == "cannot tell"
    assert real_but_tiny["verdict"] == "cannot tell"

    assert why_undecided(identical) == "no evidence", (
        "the interval on the difference contains zero, so this run cannot distinguish the two"
    )
    assert why_undecided(real_but_tiny) == "too small to matter", (
        "the interval excludes zero — the difference is real — and it is under the threshold"
    )


@pytest.mark.problem
def test_the_reason_follows_the_interval_and_not_the_size():
    """A larger difference that still fails only the evidence test is still 'no evidence'."""
    rng = random.Random(3)
    # Few runs, wide spread: a big apparent difference the evidence does not support.
    noisy = decide(draw(rng, 1000.0, 6), draw(rng, 880.0, 6), threshold=THRESHOLD)
    if noisy["verdict"] == "cannot tell" and not noisy["excludes_zero"]:
        assert why_undecided(noisy) == "no evidence"
