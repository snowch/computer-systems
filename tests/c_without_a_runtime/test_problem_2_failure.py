"""Problem 2.2 — which of these can fail, and how it says so.

Every combination of where the memory comes from and what the function hands back, because the
interesting cell is the one that only exists when you enumerate: something that can run out and
returns `void` has no way to report it.
"""

from __future__ import annotations

import itertools

import pytest

from tests.c_without_a_runtime.harness import (
    MODE_NAMES,
    R_CANNOT_FAIL,
    R_NEGATIVE,
    R_NULL,
    R_UNREPORTABLE,
    ask,
)

SOURCES = "pfsg"  # pool, free list, caller's stack, file-scope object
RETURNS = "piv"  # pointer, int status, void
EXHAUSTIBLE = set("pf")

CASES = list(itertools.product(SOURCES, RETURNS))


def expected(source: str, returns: str) -> int:
    if source not in EXHAUSTIBLE:
        return R_CANNOT_FAIL
    return {"p": R_NULL, "i": R_NEGATIVE, "v": R_UNREPORTABLE}[returns]


def test_memory_that_already_exists_cannot_run_out():
    """Scaffolding: the return type is irrelevant when there is nothing to exhaust."""
    assert all(expected(source, returns) == R_CANNOT_FAIL for source in "sg" for returns in RETURNS)


def test_the_unreportable_cell_exists_and_is_exactly_two_cases():
    """Scaffolding: the answer the enumeration is for.

    A function that can run out and returns nothing is a bug in the interface rather than in the
    body, and it is invisible unless you cross the two axes.
    """
    unreportable = [case for case in CASES if expected(*case) == R_UNREPORTABLE]
    assert unreportable == [("p", "v"), ("f", "v")]


def test_how_it_fails_follows_from_what_it_returns():
    """Scaffolding: a pointer fails as null and a status fails as negative, never the other way."""
    assert expected("f", "p") == R_NULL
    assert expected("f", "i") == R_NEGATIVE


@pytest.mark.problem
def test_each_combination_reports_the_right_failing_path(runtime):
    answered = ask(runtime, [f"f{source}{returns}" for source, returns in CASES])
    wrong = {
        f"{source}{returns}": {
            "expected": MODE_NAMES[expected(source, returns)],
            "got": MODE_NAMES.get(answered["failure"][i], answered["failure"][i]),
        }
        for i, (source, returns) in enumerate(CASES)
        if answered["failure"][i] != expected(source, returns)
    }
    assert not wrong, f"first ask whether it can run out, then how it would say so: {wrong}"
