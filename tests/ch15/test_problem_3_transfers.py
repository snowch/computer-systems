"""Problem 13.3 — does this observation transfer between the two targets?

Six things you could observe. Two of them are less obvious than they look, and sorting the list
into "structure" and "cost" gets both of them wrong.
"""

from __future__ import annotations

import pytest

from tests.ch15.harness import ask

CASES = {
    "a": 1,  # the answer: the whole reason the book can use two targets at all
    "l": 1,  # layout: both targets are LP64 and ch05 measured them agreeing
    "i": 0,  # instruction count: different instruction sets emit different numbers of them
    "c": 0,  # cache misses: one of the targets has no cache
    "p": 0,  # page faults: same mechanism, different kernels, different policies
    "t": 0,  # time: the whole of Part IV
}


def test_the_list_is_not_just_structure_against_cost():
    """Scaffolding: the instruction count is structural and does not transfer, which is the point."""
    assert CASES["i"] == 0, "instruction counts are structural and still do not transfer"
    assert CASES["l"] == 1, "layout is structural and does transfer, which is not automatic either"
    assert set(CASES.values()) == {0, 1}


@pytest.mark.problem
def test_only_what_the_two_targets_share_transfers(crossing):
    answered = ask(crossing, [f"t{what}" for what in CASES])
    wrong = {
        what: {"expected": expected, "got": answered["transfers"][what]}
        for what, expected in CASES.items()
        if answered["transfers"][what] != expected
    }
    assert not wrong, (
        "an observation transfers when it depends only on what the two targets have in common, "
        f"which is the source and the data model: {wrong}"
    )
