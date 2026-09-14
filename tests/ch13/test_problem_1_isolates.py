"""Problem 13.1 — what does comparing these two configurations isolate?

The expected answers are derived from the configuration table rather than written out, so the test
and the problem cannot drift apart and there is no key to read. Every pair of the six is asked
about, including the two that confound all three variables at once — which is the pair this book's
own two targets happen to be.
"""

from __future__ import annotations

import itertools

import pytest

from tests.ch13.harness import CONFIGS, ask


def expected(first: str, second: str) -> str:
    a, b = CONFIGS[first], CONFIGS[second]
    differing = [name for name, x, y in zip("eki", a, b, strict=True) if x != y]
    if not differing:
        return "n"
    return differing[0] if len(differing) == 1 else "x"


PAIRS = [f"{a}{b}" for a, b in itertools.product(sorted(CONFIGS), repeat=2)]


def test_every_kind_of_answer_is_reachable():
    """Scaffolding: all five verdicts occur among the pairs, so no constant can pass."""
    answers = {expected(pair[0], pair[1]) for pair in PAIRS}
    assert answers == {"e", "k", "i", "n", "x"}, answers
    assert expected("A", "D") == "x", "the book's own two targets differ in all three"


@pytest.mark.problem
def test_a_comparison_isolates_only_what_differs_once(crossing):
    answered = ask(crossing, [f"i{pair}" for pair in PAIRS])
    wrong = {
        pair: {"expected": expected(pair[0], pair[1]), "got": answered["isolates"][pair]}
        for pair in PAIRS
        if answered["isolates"][pair] != expected(pair[0], pair[1])
    }
    assert not wrong, (
        "a comparison isolates a variable only when it is the single thing that differs; "
        f"otherwise it confounds: {wrong}"
    )
