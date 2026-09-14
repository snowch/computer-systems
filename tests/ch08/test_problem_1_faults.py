"""Problem 8.1 — how many faults will these accesses cause?

Every answer follows from where the test put the bytes, so nothing is stored. The cases are chosen
around the one thing that makes this harder than counting: the program says bytes and the machine
charges pages, and the two only line up by accident.
"""

from __future__ import annotations

import pytest

from tests.ch08.harness import PAGE, count_faults

CASES = {
    "nothing at all": ([], 0),
    "a run of zero length": ([(0, 0)], 0),
    "one byte": ([(0, 1)], 1),
    "one whole page": ([(0, PAGE)], 1),
    "one whole page and one byte": ([(0, PAGE + 1)], 2),
    "two bytes that straddle": ([(PAGE - 1, 2)], 2),
    "two runs in the same page": ([(16, 8), (64, 8)], 1),
    "the same run twice": ([(0, PAGE), (0, PAGE)], 1),
    "overlapping runs across a boundary": ([(0, PAGE + 8), (PAGE - 8, 16)], 2),
    "runs out of order": ([(4 * PAGE, 1), (0, 1), (2 * PAGE, 1)], 3),
    "a long run": ([(PAGE // 2, 10 * PAGE)], 11),
}


def test_the_cases_cover_the_ways_bytes_and_pages_disagree():
    """Scaffolding: the answers are not all the same, and none is the number of runs."""
    answers = {name: expected for name, (_, expected) in CASES.items()}
    assert len(set(answers.values())) > 3, "these cases do not distinguish much"
    by_run_count = {name: len(runs) for name, (runs, _) in CASES.items()}
    assert by_run_count != answers, "counting the runs would pass, so the problem is not a problem"


@pytest.mark.problem
def test_the_prediction_matches_the_pages_the_runs_reach(policy):
    wrong = {}
    for name, (runs, expected) in CASES.items():
        got = count_faults(policy, runs)
        if got != expected:
            wrong[name] = {"expected": expected, "got": got, "runs": runs}
    assert not wrong, (
        "a first touch faults once per page reached, not once per access and not once per byte: "
        f"{wrong}"
    )
