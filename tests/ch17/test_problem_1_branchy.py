"""Checks Problem 17.1 against the compiler's own output, as recorded by this chapter's runner."""

from __future__ import annotations

import pytest

from bench.stamp import load_result
from tests.ch17.problem_1_branchy import KEEPS_A_BRANCH

RESULT = "pipeline-shapes"


def shapes() -> dict[str, dict[str, int]]:
    return load_result(RESULT)["summary"]["shapes"]


def truth() -> dict[str, bool]:
    """A data-dependent branch survived when the compiler did not if-convert it away.

    The loop-control branch is in both, so the distinguishing evidence is the conditional-select
    instruction: its presence means the `if` became arithmetic.
    """
    measured = shapes()
    return {name: measured[name]["if_converted"] == 0 for name in KEEPS_A_BRANCH}


def test_the_two_functions_really_did_compile_differently():
    """Scaffolding: if the compiler treated both the same there is nothing to predict."""
    assert len(set(truth().values())) == 2, (
        f"both were compiled the same way, so 17.1 has no answer: {shapes()}"
    )


@pytest.mark.problem
def test_the_prediction_matches_what_the_compiler_did():
    unanswered = sorted(k for k, v in KEEPS_A_BRANCH.items() if v is None)
    assert not unanswered, f"still to answer: {unanswered}"
    actual = truth()
    wrong = {
        name: {"you said": KEEPS_A_BRANCH[name], "it was": actual[name], "shape": shapes()[name]}
        for name in KEEPS_A_BRANCH
        if KEEPS_A_BRANCH[name] != actual[name]
    }
    assert not wrong, (
        "a compiler that can see both sides of an `if` are cheap replaces the branch with "
        f"arithmetic, and there is then nothing left to mispredict: {wrong}"
    )
