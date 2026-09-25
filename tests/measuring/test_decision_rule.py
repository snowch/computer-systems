"""The book's own decision rule, checked rather than asserted.

Not a problem: this is a guard on `bench.distribution`, and it runs in CI. Every "faster" in
Part V is produced by the rule exercised here, so the rule needs to be shown doing two things —
finding a real difference when given enough evidence, and declining when not given enough.

Both are stated over many seeds. A single seed says nothing: at a small run count the rule is a
coin weighted by luck, and a test pinned to one draw would pass or fail for reasons that have
nothing to do with the code.
"""

from __future__ import annotations

import random

from bench.distribution import decide

THRESHOLD = 0.02
SEEDS = 40
RESAMPLES = 400  # fewer than a published figure uses; this is about the rule, not the interval


def draw(rng: random.Random, floor: float, n: int) -> list[float]:
    return [floor + rng.expovariate(1 / (floor * 0.06)) for _ in range(n)]


def detection_rate(n: int, candidate_floor: float) -> float:
    """How often the rule calls a winner, over many independent runs."""
    called = 0
    for seed in range(SEEDS):
        rng = random.Random(seed)
        decision = decide(
            draw(rng, 1000.0, n),
            draw(rng, candidate_floor, n),
            threshold=THRESHOLD,
            resamples=RESAMPLES,
        )
        called += decision["verdict"] != "cannot tell"
    return called / SEEDS


def test_a_real_difference_needs_enough_runs_to_be_seen():
    """The chapter's claim: the same difference is invisible at a low run count and plain at a high one.

    A 4% difference against a 6% spread. At six runs the evidence mostly does not support a
    verdict; by two hundred it always does. That gap is the whole reason the chapter asks how many
    runs rather than assuming one is enough.
    """
    few = detection_rate(6, 960.0)
    many = detection_rate(200, 960.0)

    assert few < 0.6, (
        f"at six runs the rule called a winner {few:.0%} of the time. It should mostly decline: "
        "if it does not, the rule is claiming more than six samples can support"
    )
    assert many == 1.0, (
        f"at two hundred runs the rule called a winner only {many:.0%} of the time, so it is "
        "failing to see a difference the evidence does support"
    )
    assert few < many, "more runs must not make a real difference harder to see"


def test_the_rule_does_not_invent_a_difference_that_is_not_there():
    """Two samples from the same distribution, at a run count that easily finds a real 4%."""
    rate = detection_rate(200, 1000.0)
    assert rate == 0.0, (
        f"the rule called a winner {rate:.0%} of the time between two identical distributions"
    )


def test_a_difference_under_the_threshold_is_never_called():
    """Real, repeatable, and smaller than anybody said they would care about."""
    rate = detection_rate(400, 995.0)  # 0.5% apart, threshold 2%
    assert rate == 0.0, (
        "a difference under the threshold was called a winner, which is the rule's second half "
        "not being applied"
    )
