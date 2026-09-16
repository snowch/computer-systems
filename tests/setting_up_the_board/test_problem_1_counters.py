"""Checks Problem 1.1. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.setting_up_the_board.problem_1_counters import counts_hardware_events


def report(value, supported=True, emulated=False, multiplexed=False) -> dict:
    return {
        "value": value,
        "supported": supported,
        "emulated": emulated,
        "multiplexed": multiplexed,
    }


CASES = [
    ("a plain hardware count", report(1_234_567), True),
    ("the event is not supported at all", report(None, supported=False), False),
    ("a number, for an event the kernel says does not exist", report(0, supported=False), False),
    ("the kernel computed it rather than reading it", report(1_234_567, emulated=True), False),
    ("counted for part of the run and scaled up", report(1_234_567, multiplexed=True), False),
    ("a real count that happens to be zero", report(0), True),
]


def test_a_number_alone_does_not_decide_it():
    """Scaffolding: two cases print a number and disagree, or the problem is `value is not None`."""
    printed = [(d, r, e) for d, r, e in CASES if r["value"] is not None]
    assert {e for _, _, e in printed} == {True, False}, "printing a number must not settle it"


def test_zero_is_not_the_same_as_absent():
    """Scaffolding: a real counter reading zero is a measurement; an absent one is not."""
    assert dict(CASES[-1][1])["value"] == 0 and CASES[-1][2] is True


@pytest.mark.problem
@pytest.mark.parametrize(("description", "payload", "expected"), CASES, ids=[c[0] for c in CASES])
def test_only_a_real_count_counts(description, payload, expected):
    try:
        answer = counts_hardware_events(payload)
    except NotImplementedError:
        pytest.fail(
            "Problem 1.1 is not solved — see tests/setting_up_the_board/problem_1_counters.py"
        )
    assert answer is expected, f"{description}: you said {answer}, and the chapter says {expected}"
