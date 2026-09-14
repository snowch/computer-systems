"""Checks Problem 1.1. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.ch01.problem_1_stages import which_stage_wrote_this

CASES = [
    (
        "a line directive naming a header nobody typed",
        '# 33 "/usr/include/stdio.h" 2 3 4\nextern int printf (const char *__restrict __fmt, ...);',
        "preprocess",
    ),
    (
        "a mnemonic with a label, and no addresses at all",
        "sysfs_sum_folded:\n\tli\ta0,2016\n\tret",
        "compile",
    ),
    (
        "offsets from the start of one section, and a symbol it cannot place",
        "0000000000000000 <sysfs_sum_folded>:\n   0:\tli\ta0,2016\n   4:\tret\n"
        "RELOCATION RECORDS FOR [.text]:\n0000000000000010 R_RISCV_CALL_PLT  printf",
        "assemble",
    ),
    (
        "a real address, and nothing left undefined",
        "00000000000104c8 <main>:\n   104c8:\taddi\tsp,sp,-32\n   104cc:\tjal\t10a3c <printf>",
        "link",
    ),
]


@pytest.mark.problem
@pytest.mark.parametrize(
    ("description", "fragment", "expected"), CASES, ids=[case[0] for case in CASES]
)
def test_the_reader_can_tell_the_stages_apart(description: str, fragment: str, expected: str):
    assert which_stage_wrote_this(fragment) == expected, (
        f"{description}: this came out of the {expected} stage"
    )


def test_every_stage_appears_in_the_puzzle():
    """Scaffolding: the problem is answerable, and covers all four stages rather than three."""
    assert {case[2] for case in CASES} == {"preprocess", "compile", "assemble", "link"}
