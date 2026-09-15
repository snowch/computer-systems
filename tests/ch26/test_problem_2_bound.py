"""Problem 19.2 — what Part IV's instruction count says the call cannot beat.

Two things are being checked. The arithmetic, which is a bound rather than an estimate and so has
to round once at the end; and the shape, which is that halving the IPC doubles the floor.
"""

from __future__ import annotations

import pytest

from tests.ch26.harness import ask

# (instructions, ipc_x100, mhz)
CASES = {
    "ch13's path at IPC 1.5": (83, 150, 2_400),
    "ch13's path at IPC 1.0": (83, 100, 2_400),
    "ch13's path at IPC 0.5": (83, 50, 2_400),
    "ch13's path on a slower clock": (83, 250, 1_500),
    "one instruction": (1, 100, 1_000),
    "a cycle per megahertz": (2_400, 100, 2_400),
    "a long path": (10_000, 175, 2_400),
}


def expected(instructions: int, ipc_x100: int, mhz: int) -> int:
    """cycles = instructions / ipc; nanoseconds = cycles * 1000 / mhz — as one division."""
    return (instructions * 100 * 1_000) // (ipc_x100 * mhz)


def rounded_twice(instructions: int, ipc_x100: int, mhz: int) -> int:
    return ((instructions * 100) // ipc_x100) * 1_000 // mhz


def test_rounding_twice_gives_a_different_answer():
    """Scaffolding: if it did not, the instruction to divide once would be decoration."""
    disagree = [name for name, case in CASES.items() if expected(*case) != rounded_twice(*case)]
    assert disagree, "pick cases where the intermediate rounding is visible, or drop the rule"


def test_halving_the_ipc_doubles_the_floor():
    """Scaffolding: the bound's shape, which is the part a reader should be able to predict."""
    fast = expected(*CASES["ch13's path at IPC 1.5"])
    slow = expected(*CASES["ch13's path at IPC 0.5"])
    assert slow == pytest.approx(3 * fast, rel=0.02)


@pytest.mark.problem
def test_the_bound_is_the_instructions_divided_by_what_the_machine_retires(oscost):
    names = sorted(CASES)
    answered = ask(oscost, [f"b{','.join(str(n) for n in CASES[name])}" for name in names])
    wrong = {
        name: {"expected": expected(*CASES[name]), "got": answered["bound"][i]}
        for i, name in enumerate(names)
        if answered["bound"][i] != expected(*CASES[name])
    }
    assert not wrong, (
        "the instructions have to be retired, and nothing else in this number is allowed to "
        f"be: {wrong}"
    )
