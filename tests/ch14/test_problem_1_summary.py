"""Problem 14.1 — report the distribution rather than a number.

The expected answers are computed from the sample sets by the same definitions the stub states, so
the key is derived rather than written down. The even-length cases are the ones that matter: the
median of an even set is a sample that happened, not an average of two that did.
"""

from __future__ import annotations

import pytest

from tests.ch14.harness import ask

SETS = [
    [5],
    [5, 1, 3],
    [4, 1, 3, 2],
    [10] * 10,
    [100, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    list(range(1, 21)),
]


def expected(samples: list[int]) -> tuple[int, int, int, int]:
    ordered = sorted(samples)
    count = len(ordered)
    if count == 0:
        return (0, 0, 0, 0)
    return (
        ordered[0],
        ordered[count // 2],
        ordered[min((count * 9) // 10, count - 1)],
        sum(ordered) // count,
    )


def test_the_sets_exercise_the_definitions_that_go_wrong():
    """Scaffolding: an even-length set, a constant set, and one dominated by a single outlier."""
    assert expected([4, 1, 3, 2])[1] == 3, "the median of an even set is the upper middle sample"
    outlier = expected([100, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert outlier[0] == 1 and outlier[3] > 1, "the mean must move where the minimum does not"


@pytest.mark.problem
def test_the_summary_matches_the_stated_definitions(measuring):
    commands = [f"s{i},{'.'.join(str(v) for v in s)}" for i, s in enumerate(SETS)]
    answered = ask(measuring, commands)
    wrong = {
        str(s): {"expected": expected(s), "got": answered["summary"][i]}
        for i, s in enumerate(SETS)
        if answered["summary"][i] != expected(s)
    }
    assert not wrong, f"min, median, p90 and mean, by the definitions in the stub: {wrong}"
