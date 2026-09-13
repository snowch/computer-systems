"""Checks Problem 0.1. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.ch00.problem_1_trust import can_you_publish_this_timing


def result(target: str, kind: str, measured_under: str) -> dict:
    return {
        "target": target,
        "machine": {"kind": kind, "arch": "riscv64", "measured_under": measured_under},
        "summary": {"loop_ns": 42.0},
    }


CASES = [
    # (description, result, publishable?)
    ("the board, natively", result("host", "board", "native"), True),
    ("a Linux guest inside QEMU", result("host", "qemu", "emulation"), False),
    ("user-mode emulation on a laptop", result("host", "qemu-user", "emulation"), False),
    ("an x86-64 CI runner", result("host", "other", "native"), False),
    ("xv6 under QEMU, whatever it says", result("xv6", "qemu", "emulation"), False),
]


@pytest.mark.problem
@pytest.mark.parametrize(
    ("description", "payload", "expected"), CASES, ids=[case[0] for case in CASES]
)
def test_publishable(description: str, payload: dict, expected: bool):
    try:
        answer = can_you_publish_this_timing(payload)
    except NotImplementedError:
        pytest.fail("Problem 0.1 is not solved yet — see tests/ch00/problem_1_trust.py")
    assert answer is expected, (
        f"{description}: you said {answer}, and chapter 0 says {expected}. "
        "A timing is worth printing only when the machine that produced it was the machine the "
        "book claims to have measured."
    )


def test_the_problem_is_wired_up():
    """Scaffolding, not the problem: the stub imports and every case is a distinct scenario.

    CI runs this and deselects the problem itself. The book is responsible for handing you a
    problem that runs; making it pass is yours.
    """
    assert callable(can_you_publish_this_timing)
    assert len({case[0] for case in CASES}) == len(CASES)
    assert sum(1 for case in CASES if case[2]) == 1, "exactly one of these is publishable"
