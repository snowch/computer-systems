"""Problem 12.3 — is this ordering safe at every point a crash could happen?

Only one of the six orderings is, and the unsafe ones are the ones that look reasonable. The test
asks about all of them at once, because a rule that gets one right by luck is not a rule.
"""

from __future__ import annotations

import pytest

from tests.ch19.harness import ask

#: order written -> is every prefix survivable?
CASES = {
    "lhb": 1,  # log the blocks, commit, then put them home: the one that works
    "lbh": 0,  # homes updated before the transaction is committed: a crash leaves half of it
    "hlb": 0,  # committed before the log holds anything: recovery replays rubbish
    "blh": 0,  # homes first, which is the version with no log at all wearing one
    "bhl": 0,
    "hbl": 0,
}


def test_exactly_one_ordering_is_safe():
    """Scaffolding: the problem is not "which looks sensible", so only one may pass."""
    assert sum(CASES.values()) == 1, "if more than one ordering worked the log would be optional"
    assert CASES["lhb"] == 1


@pytest.mark.problem
def test_only_the_ordering_whose_every_prefix_survives_is_safe(filesystem):
    answered = ask(filesystem, [f"o{order}" for order in CASES])
    wrong = {
        order: {"expected": expected, "got": answered["safe"][order]}
        for order, expected in CASES.items()
        if answered["safe"][order] != expected
    }
    assert not wrong, (
        "an ordering is safe when every prefix of it is survivable, not when the end state is "
        f"right: {wrong}"
    )
