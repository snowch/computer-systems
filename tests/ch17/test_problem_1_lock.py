"""Problem 10.1 — a lock that is merely usually right is not a lock.

Four threads take it eight hundred thousand times between them and increment an ordinary,
deliberately non-atomic counter inside it. If the lock works the total is exactly what was asked
for; if it does not, updates are lost in quantity — the unlocked version of this loses most of
them, which is the measurement the chapter opens with.

Run three times, because the failure mode being ruled out is intermittent by nature and once is
not evidence about a lock.
"""

from __future__ import annotations

import pytest

from tests.ch17.harness import ask

ROUNDS = 3


def test_the_harness_counts_something_worth_losing(locking):
    """Scaffolding: the hammer runs and reports both numbers, so the problem has a target."""
    answered = ask(locking, ["h"])
    assert len(answered["hammer"]) == 1
    expected, _ = answered["hammer"][0]
    assert expected >= 100_000, "too few increments to catch a lock that is only usually right"


@pytest.mark.problem
def test_no_update_is_lost_in_three_separate_runs(locking):
    answered = ask(locking, ["h"] * ROUNDS)
    short = [
        {"asked for": expected, "counted": got}
        for expected, got in answered["hammer"]
        if got != expected
    ]
    assert not short, (
        "an increment inside the critical section went missing, so two threads were inside at "
        f"once: {short}"
    )
