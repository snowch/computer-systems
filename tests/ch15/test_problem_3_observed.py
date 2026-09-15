"""Problem 8.3 — when does a program that asks for too much find out?

This is the cost of laziness that is not measured in faults, and the reason an operating system
that overcommits needs something to kill processes with. Each answer follows from the numbers the
test supplies: whether the request fits, whether the touches fit, and which policy was used.
"""

from __future__ import annotations

import pytest

from tests.ch15.harness import AT_REQUEST, AT_TOUCH, EAGER, LAZY, NEVER, ask

#: (policy, requested, touched, available) -> where the shortage becomes visible.
CASES = {
    (EAGER, 10, 10, 100): NEVER,
    (EAGER, 200, 10, 100): AT_REQUEST,
    (EAGER, 200, 0, 100): AT_REQUEST,
    (LAZY, 10, 10, 100): NEVER,
    (LAZY, 200, 10, 100): NEVER,
    (LAZY, 200, 200, 100): AT_TOUCH,
    (LAZY, 200, 101, 100): AT_TOUCH,
    (LAZY, 200, 100, 100): NEVER,
}


def test_the_cases_separate_the_two_policies():
    """Scaffolding: the same request has different answers under the two policies."""
    eager = {k: v for k, v in CASES.items() if k[0] == EAGER}
    lazy = {k: v for k, v in CASES.items() if k[0] == LAZY}
    assert AT_REQUEST in eager.values() and AT_REQUEST not in lazy.values()
    assert AT_TOUCH in lazy.values() and AT_TOUCH not in eager.values()
    assert CASES[(EAGER, 200, 10, 100)] != CASES[(LAZY, 200, 10, 100)], (
        "the headline case must differ, or the problem says nothing"
    )


@pytest.mark.problem
def test_laziness_moves_the_failure_somewhere_it_cannot_be_handled(policy):
    commands = [f"o{p},{r},{t},{a}" for p, r, t, a in CASES]
    answered = ask(policy, commands)
    names = {AT_REQUEST: "at the request", AT_TOUCH: "at the touch", NEVER: "never"}
    wrong = {
        f"policy {p}, asked {r}, touched {t}, had {a}": {
            "expected": names[expected],
            "got": names.get(
                answered["observed"][(p, r, t, a)], answered["observed"][(p, r, t, a)]
            ),
        }
        for (p, r, t, a), expected in CASES.items()
        if answered["observed"][(p, r, t, a)] != expected
    }
    assert not wrong, (
        "an eager request fails where the program can check it; a lazy one succeeds and fails "
        f"later, on an ordinary store, where it cannot: {wrong}"
    )
