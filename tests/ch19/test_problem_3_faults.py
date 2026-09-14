"""Problem 19.3 — none, minor, major, fatal, from four facts and a stated precedence.

All sixteen combinations, because the precedence is the content: fatal overrides everything, a
translation that already exists costs nothing, and only then does the minor/major split arise —
decided by whether the data is in memory, which is the difference worth orders of magnitude.
"""

from __future__ import annotations

import itertools

import pytest

from tests.ch19.harness import KIND_NAMES, O_FATAL, O_MAJOR, O_MINOR, O_NONE, ask

CASES = list(itertools.product((0, 1), repeat=4))  # (requested, mapped, resident, zero_fill)


def expected(requested: int, mapped: int, resident: int, zero_fill: int) -> int:
    if not requested:
        return O_FATAL
    if mapped:
        return O_NONE
    if resident or zero_fill:
        return O_MINOR
    return O_MAJOR


def test_exactly_one_combination_in_sixteen_has_to_wait_for_storage():
    """Scaffolding: a major fault is the rarest thing in the table and the most expensive."""
    majors = [case for case in CASES if expected(*case) == O_MAJOR]
    assert majors == [(1, 0, 0, 0)]


def test_an_unrequested_address_is_fatal_however_good_it_looks():
    """Scaffolding: the precedence, which is the only part a reader can get wrong twice."""
    assert expected(0, 1, 1, 1) == O_FATAL
    assert all(expected(*case) == O_FATAL for case in CASES if case[0] == 0)


def test_a_page_that_owes_only_zeroes_is_minor_with_nothing_resident():
    """Scaffolding: 'minor' does not mean the data was found — it means storage was not read."""
    assert expected(1, 0, 0, 1) == O_MINOR
    assert expected(1, 0, 1, 0) == O_MINOR


@pytest.mark.problem
def test_every_combination_is_classified(oscost):
    answered = ask(oscost, ["f" + "".join(str(bit) for bit in case) for case in CASES])
    wrong = {
        "".join(str(bit) for bit in case): {
            "expected": KIND_NAMES[expected(*case)],
            "got": KIND_NAMES.get(answered["fault"][i], answered["fault"][i]),
        }
        for i, case in enumerate(CASES)
        if answered["fault"][i] != expected(*case)
    }
    assert not wrong, (
        "requested, mapped, resident, zero_fill — and the order the rules are applied in is the "
        f"answer: {wrong}"
    )
