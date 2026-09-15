"""Checks Problem 1.2. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.reading_a_listing.problem_2_memory import reaches_memory

#: operand, as a listing prints it -> does reading it mean going to memory?
CASES = {
    "a0": False,
    "sp": False,
    "x9": False,
    "4(a0)": True,
    "0(sp)": True,
    "-16(s0)": True,
    "[x2]": True,
    "[x2, #8]": True,
    "#16": False,
    "x0": False,
    "8(a0)": True,
}


def test_the_near_pair_is_in_the_table():
    """Scaffolding: `a0` and `4(a0)` differ by punctuation and must disagree."""
    assert CASES["a0"] != CASES["4(a0)"]
    assert CASES["#16"] != CASES["[x2, #8]"], "a literal and a bracket must not be confused"


def test_both_instruction_sets_are_represented():
    """Scaffolding: parentheses are RISC-V and brackets are AArch64; one alone tests half of it."""
    assert any("(" in k for k in CASES) and any("[" in k for k in CASES)


@pytest.mark.problem
@pytest.mark.parametrize("operand", sorted(CASES), ids=sorted(CASES))
def test_only_the_bracketed_forms_reach_memory(operand):
    try:
        answer = reaches_memory(operand)
    except NotImplementedError:
        pytest.fail("Problem 1.2 is not solved — see tests/reading_a_listing/problem_2_memory.py")
    assert answer is CASES[operand], (
        f"{operand!r}: you said {answer}, the notation says {CASES[operand]}"
    )
