"""Problem 11.3 — what order does each policy actually run them in?

The expected orders follow from the burst lengths the test chose and from the rules in the stub,
so there is nothing to look up. The same three jobs under three policies give three answers, which
is the point: a policy is not a detail.
"""

from __future__ import annotations

import pytest

from tests.scheduling_and_context_switches.harness import ask

JOBS = [3, 1, 2]

CASES = {
    "f": [0, 0, 0, 1, 2, 2],
    "s": [1, 2, 2, 0, 0, 0],
    "r": [0, 1, 2, 0, 2, 0],
}


def test_the_three_policies_disagree_about_these_jobs():
    """Scaffolding: the jobs are chosen so that no two policies give the same order."""
    assert len({tuple(order) for order in CASES.values()}) == 3
    for order in CASES.values():
        assert sorted(order) == sorted([0] * 3 + [1] + [2] * 2), "every job must run to completion"


@pytest.mark.problem
@pytest.mark.parametrize("policy", sorted(CASES))
def test_each_policy_produces_its_own_order(policy, scheduling):
    answered = ask(scheduling, [f"o{policy},{'.'.join(str(b) for b in JOBS)}"])
    got = answered["order"][0]
    assert got == CASES[policy], (
        f"policy {policy!r} on bursts {JOBS} should run {CASES[policy]} and produced {got}"
    )
