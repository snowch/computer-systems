"""Problem 2.3 — how many reads the compiler is allowed to leave.

The three answers are a constant, one, and zero, and the scaffolding pins what separates them: only
the volatile case grows with the number of reads in the source.
"""

from __future__ import annotations

import pytest

from tests.ch02.harness import ask

# (reads, qualified, used)
CASES = {
    "volatile, used": (4, 1, 1),
    "volatile, discarded": (4, 1, 0),
    "plain, used": (4, 0, 1),
    "plain, discarded": (4, 0, 0),
    "a single volatile read": (1, 1, 1),
    "a single plain read": (1, 0, 1),
    "a long volatile loop": (1000, 1, 1),
    "a long plain loop": (1000, 0, 1),
}


def expected(reads: int, qualified: int, used: int) -> int:
    if qualified:
        return reads
    return 1 if used else 0


def test_only_the_volatile_case_grows_with_the_source():
    """Scaffolding: the property that separates a device register from a variable."""
    assert expected(1000, 1, 1) == 1000
    assert expected(1000, 0, 1) == 1
    assert expected(4, 0, 1) == expected(1000, 0, 1)


def test_a_discarded_volatile_read_still_happens():
    """Scaffolding: the case that shows volatile is about the access and not about the value.

    Reading a device register to clear it is a real thing, and the value goes nowhere.
    """
    assert expected(4, 1, 0) == 4
    assert expected(4, 0, 0) == 0


def test_at_one_read_volatile_and_plain_agree_when_the_value_is_used():
    """Scaffolding: the boundary. The qualifier costs nothing until there is more than one."""
    assert expected(1, 1, 1) == expected(1, 0, 1) == 1


@pytest.mark.problem
def test_the_permitted_count_follows_the_qualifier(runtime):
    names = sorted(CASES)
    answered = ask(runtime, [f"v{','.join(str(n) for n in CASES[name])}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["reads"][i]}
        for i, name in enumerate(names)
        if answered["reads"][i] != expected(*CASES[name])
    }
    assert not wrong, (
        "volatile keeps every access; without it one read of an unchanging address suffices, "
        f"and a discarded one need not happen: {wrong}"
    )
