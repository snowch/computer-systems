"""Problem 8.2 — what should the handler do about this fault?

Every answer follows from where the test put the process's boundary and from whether it says the
page is already there, so nothing is stored. Three of the cases are the ones a handler written
from the happy path gets wrong.
"""

from __future__ import annotations

import pytest

from tests.ch15.harness import ALLOCATE, FETCH, KILL, LOAD, PAGE, PANIC, STORE, ask

#: One process, whose heap runs up to SZ. Both numbers are this test's choice.
SZ = 64 * PAGE
UNMAPPED, MAPPED = 0, 1

#: (cause, address, already mapped) -> what the handler should decide.
CASES = {
    (STORE, 0, UNMAPPED): ALLOCATE,
    (LOAD, 12 * PAGE, UNMAPPED): ALLOCATE,
    (STORE, 12 * PAGE, UNMAPPED): ALLOCATE,
    (STORE, SZ - 1, UNMAPPED): ALLOCATE,
    (STORE, SZ, UNMAPPED): KILL,
    (LOAD, SZ, UNMAPPED): KILL,
    (FETCH, SZ + 8, UNMAPPED): KILL,
    # Already there: a permission was refused, and allocating over it destroys live data.
    (STORE, 12 * PAGE, MAPPED): KILL,
    (LOAD, 4 * PAGE, MAPPED): KILL,
    # Not a page fault. scause 8 is a system call, and it has no business arriving here.
    (8, 0, UNMAPPED): PANIC,
}


def test_the_cases_are_the_three_a_happy_path_gets_wrong():
    """Scaffolding: the boundary, the already-mapped page and the wrong cause all change the answer."""
    assert CASES[(STORE, SZ - 1, UNMAPPED)] != CASES[(STORE, SZ, UNMAPPED)], "the boundary matters"
    assert CASES[(STORE, 12 * PAGE, UNMAPPED)] != CASES[(STORE, 12 * PAGE, MAPPED)], (
        "the same address must decide differently depending on whether the page is there"
    )
    assert PANIC in CASES.values(), "a cause that is not a page fault must be distinguishable"


@pytest.mark.problem
def test_the_handler_grants_what_was_asked_for_and_nothing_else(policy):
    commands = [f"a{cause},{va:#x},{SZ:#x},{mapped}" for cause, va, mapped in CASES]
    answered = ask(policy, commands)
    names = {ALLOCATE: "allocate", KILL: "kill", PANIC: "panic"}
    wrong = {
        f"cause {cause} at {va:#x}{' (mapped)' if mapped else ''}": {
            "expected": names[expected],
            "got": names.get(answered["action"][key], answered["action"][key]),
        }
        for key, expected in CASES.items()
        for cause, va, mapped in [key]
        if answered["action"][key] != expected
    }
    assert not wrong, (
        f"the process asked for everything below {SZ:#x} and nothing at or above it; a page that "
        f"is already mapped was never a first touch: {wrong}"
    )
