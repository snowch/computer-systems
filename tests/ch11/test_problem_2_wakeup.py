"""Problem 11.2 — does the sleeper wake, or was the wakeup aimed at nobody?

Each sequence is one the test wrote, so every answer follows from it. The pair that matters is the
two orderings of the same six events: one loses the wakeup and one cannot.
"""

from __future__ import annotations

import pytest

from tests.ch11.harness import ask

#: event string -> was the wakeup lost (sleeper still asleep, condition true)?
CASES = {
    # The condition was already true, so the sleeper never sleeps.
    "cm": 0,
    # Correct: the lock is held across the check and the sleep, so the waker cannot get between.
    "LcsmwU": 0,
    # The bug: the sleeper lets go of the lock before sleeping, and the waker fits in the gap.
    "LcUmws": 1,
    # The same gap, without the condition being made true: nothing to miss.
    "LcUws": 0,
    # Woken after sleeping is the ordinary case.
    "Lcsmw": 0,
    # Two wakeups, one of them wasted, but the second arrives after the sleep.
    "LcUmwsw": 0,
}


def test_the_two_orderings_of_the_same_events_differ():
    """Scaffolding: the problem is about order, so the same events must give different answers."""
    assert sorted("LcsmwU") == sorted("LcUmws"), "the pair must use the same events"
    assert CASES["LcsmwU"] != CASES["LcUmws"], "and must not have the same answer"


@pytest.mark.problem
def test_a_wakeup_aimed_before_the_sleep_hits_nothing(scheduling):
    ordered = list(CASES)
    answered = ask(scheduling, [f"l{i},{events}" for i, events in enumerate(ordered)])
    wrong = {
        events: {"expected": CASES[events], "got": answered["lost"][i]}
        for i, events in enumerate(ordered)
        if answered["lost"][i] != CASES[events]
    }
    assert not wrong, (
        "a wakeup aimed at a thread that has not slept yet hits nothing and is not repeated: "
        f"{wrong}"
    )
