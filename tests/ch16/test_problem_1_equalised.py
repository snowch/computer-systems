"""Checks Problems 16.1 and 16.2 against what the compiler actually produced.

The key is the stamped result, which CI regenerates on every push, so these are graded against a
compiler rather than against an opinion — and a future compiler that changes its mind changes the
right answer rather than making the book wrong.
"""

from __future__ import annotations

import pytest

from bench.stamp import load_result
from tests.ch16.problem_1_equalised import BACKFIRED, BACKFIRED_AT_O3, EQUALISED_AT_O2

RESULT = "loops-aarch64"


def counts(level: str) -> dict[str, int]:
    raw = load_result(RESULT)["summary"]["instructions"][level]
    return {name.removeprefix("sysfs_loop_"): value for name, value in raw.items()}


def actual_groups(level: str) -> set[frozenset[str]]:
    by_count: dict[int, set[str]] = {}
    for name, value in counts(level).items():
        by_count.setdefault(value, set()).add(name)
    return {frozenset(group) for group in by_count.values()}


def test_the_compiler_really_did_equalise_some_and_not_others():
    """Scaffolding: the problem is only a problem if the answer is neither all nor none."""
    groups = actual_groups("-O2")
    assert 1 < len(groups) < len(counts("-O2")), (
        "the five variants must fall into more than one group and fewer than five, or there is "
        f"nothing to predict: {groups}"
    )


def test_some_variant_is_worse_than_writing_it_plainly():
    """Scaffolding: problem 16.2 needs a backfiring transformation to exist."""
    at_o2 = counts("-O2")
    worse = [name for name, value in at_o2.items() if value > at_o2["plain"]]
    assert worse, "no hand-optimisation cost instructions, so 16.2 has no answer"


@pytest.mark.problem
def test_the_predicted_groups_are_the_ones_the_compiler_made():
    assert EQUALISED_AT_O2 is not None, "still to answer: EQUALISED_AT_O2"
    claimed = {frozenset(group) for group in EQUALISED_AT_O2}
    flat = [name for group in EQUALISED_AT_O2 for name in group]
    assert sorted(flat) == sorted(counts("-O2")), (
        f"every variant must appear exactly once: {sorted(flat)}"
    )
    assert claimed == actual_groups("-O2"), (
        f"the compiler grouped them as {sorted(sorted(g) for g in actual_groups('-O2'))}"
    )


@pytest.mark.problem
def test_the_backfiring_transformation_is_named_and_its_fate_at_o3_is_right():
    assert BACKFIRED is not None, "still to answer: BACKFIRED"
    assert BACKFIRED_AT_O3 is not None, "still to answer: BACKFIRED_AT_O3"

    at_o2, at_o3 = counts("-O2"), counts("-O3")
    assert at_o2[BACKFIRED] > at_o2["plain"], (
        f"{BACKFIRED!r} is not worse than plain at -O2: {at_o2[BACKFIRED]} against {at_o2['plain']}"
    )
    moved = at_o3[BACKFIRED] - at_o2[BACKFIRED]
    expected = "same" if moved == 0 else ("better" if moved < 0 else "worse")
    assert expected == BACKFIRED_AT_O3, (
        f"{BACKFIRED!r} went from {at_o2[BACKFIRED]} instructions at -O2 to {at_o3[BACKFIRED]} "
        "at -O3"
    )
