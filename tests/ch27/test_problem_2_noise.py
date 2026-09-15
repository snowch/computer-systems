"""Problem 20.2 — the number of samples a claim needs.

The key is the closed form, derived here rather than stored, and the scaffolding asserts the two
properties that make it worth knowing: halving the width you want costs four times the samples,
and a rare symbol is expensive to resolve in absolute terms but cheap relative to its own size.
"""

from __future__ import annotations

import math

import pytest

from tests.ch27.harness import ask

# (share per mille, resolve per mille)
CASES = {
    "a tenth of the time, to a percent": (100, 10),
    "a tenth of the time, to half a percent": (100, 5),
    "half the time, to a percent": (500, 10),
    "half a percent, to half a percent": (5, 5),
    "a fifth, to a fifth": (200, 200),
    "almost everything, to a percent": (950, 10),
    "a tenth of a percent, to that": (1, 1),
}


def expected(share: int, resolve: int) -> int:
    """n such that 2*sqrt(p(1-p)/n) <= e, in per mille, rounded up."""
    return -(-(4 * share * (1_000 - share)) // (resolve * resolve))


def test_the_closed_form_is_what_the_definition_says():
    """Scaffolding: the integer expression must agree with the floating-point statement."""
    for share, resolve in CASES.values():
        p, e = share / 1_000, resolve / 1_000
        n = expected(share, resolve)
        assert 2 * math.sqrt(p * (1 - p) / n) <= e + 1e-12, (share, resolve, n)
        assert n == 1 or 2 * math.sqrt(p * (1 - p) / (n - 1)) > e, "n must be the smallest"


def test_halving_the_width_costs_four_times_the_samples():
    """Scaffolding: the shape, which is the part worth carrying around."""
    wide = expected(*CASES["a tenth of the time, to a percent"])
    narrow = expected(*CASES["a tenth of the time, to half a percent"])
    assert narrow == pytest.approx(4 * wide, rel=0.01)


def test_a_rare_symbol_is_cheap_to_resolve_only_in_its_own_terms():
    """Scaffolding: the trap in reading the answer.

    Half a percent to half a percent needs fewer samples than a tenth to a percent — and is a far
    weaker claim, because the width is the same size as the thing being measured.
    """
    assert expected(*CASES["half a percent, to half a percent"]) < expected(
        *CASES["a tenth of the time, to a percent"]
    )


@pytest.mark.problem
def test_the_sample_count_follows_the_binomial_error(profiler):
    names = sorted(CASES)
    answered = ask(profiler, [f"n{CASES[name][0]},{CASES[name][1]}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["needed"][i]}
        for i, name in enumerate(names)
        if answered["needed"][i] != expected(*CASES[name])
    }
    assert not wrong, f"two standard errors of a binomial share, in per mille, rounded up: {wrong}"
