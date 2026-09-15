"""Checks Problem 6.2 against the kernel that is actually built.

The count is read out of the trampoline rather than stored, so a reader who changes the kernel and
re-runs is graded against their kernel. The list of unsaved registers is checked for being
*right*, not merely the right length: each name has to be one the disassembly does not store.
"""

from __future__ import annotations

import pytest

from bench import xv6
from bench.run_traps import measure_path
from tests.ch13.problem_2_registers import NOT_SAVED, SAVED_BY_USERVEC, TOTAL_REGISTERS

pytestmark = pytest.mark.xv6


@pytest.fixture(scope="module")
def path():
    xv6.build()
    return measure_path()


@pytest.mark.problem
def test_the_register_file_is_the_size_the_reader_says():
    assert TOTAL_REGISTERS is not None, "Problem 6.2: TOTAL_REGISTERS is still None"
    assert TOTAL_REGISTERS == 32, (
        "RV64I has a fixed-size integer register file and the number is in the unprivileged "
        "specification"
    )


@pytest.mark.problem
def test_the_reader_counted_what_uservec_saves(path):
    assert SAVED_BY_USERVEC is not None, "Problem 6.2: SAVED_BY_USERVEC is still None"
    assert path["uservec"]["register_stores"] == SAVED_BY_USERVEC, (
        f"uservec stores {path['uservec']['register_stores']} registers in the kernel as built"
    )


@pytest.mark.problem
def test_the_unsaved_registers_account_for_the_difference(path):
    assert NOT_SAVED, "Problem 6.2: NOT_SAVED is still empty"
    assert TOTAL_REGISTERS is not None and SAVED_BY_USERVEC is not None
    missing = TOTAL_REGISTERS - SAVED_BY_USERVEC
    assert len(NOT_SAVED) == missing, (
        f"{missing} registers are not stored and you named {len(NOT_SAVED)}. "
        "Each one is unsaved for a reason; name them all."
    )
    assert len(set(NOT_SAVED)) == len(NOT_SAVED), "you named the same register twice"


def test_the_path_is_measurable(path):
    """Scaffolding: the problem needs a trampoline that stores something."""
    assert path["uservec"]["register_stores"] > 0, path
