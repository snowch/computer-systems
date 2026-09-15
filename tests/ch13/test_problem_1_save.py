"""Problem 11.1 — must the switch save this register?

The answers follow from chapter 4's calling convention, which the reader already has, applied to
the fact that a context switch is an ordinary call. Nothing here is a property of xv6.
"""

from __future__ import annotations

import pytest

from tests.ch13.harness import ask

#: (ABI class, still needed afterwards) -> must `swtch` itself preserve it?
CASES = {
    ("s", 1): 1,  # callee-saved and live: the switch is the callee, so it is the switch's job
    ("s", 0): 1,  # callee-saved: the promise is unconditional, live or not
    ("r", 1): 1,  # return address and stack pointer: without these there is nothing to return to
    ("a", 1): 0,  # caller-saved: whoever called the switch already dealt with it
    ("a", 0): 0,
    ("t", 1): 0,  # a temporary is by definition not expected to survive a call
    ("t", 0): 0,
}


def test_the_two_halves_of_the_convention_are_both_asked_about():
    """Scaffolding: the answer must depend on the class, not on liveness alone."""
    assert CASES[("s", 0)] != CASES[("a", 0)], "the class has to decide it"
    assert CASES[("a", 1)] == CASES[("a", 0)], "a caller-saved register is the caller's problem"
    assert sum(CASES.values()) not in (0, len(CASES)), "a constant answer would pass"


@pytest.mark.problem
def test_the_switch_saves_exactly_what_the_convention_leaves_it(scheduling):
    answered = ask(scheduling, [f"v{cls}{int(live)}" for cls, live in CASES])
    wrong = {
        f"class {cls!r}{' (live)' if live else ''}": {
            "expected": expected,
            "got": answered["save"][f"{cls}{int(live)}"],
        }
        for (cls, live), expected in CASES.items()
        if answered["save"][f"{cls}{int(live)}"] != expected
    }
    assert not wrong, (
        "a context switch is a function call, so the convention has already decided most of "
        f"this: {wrong}"
    )
