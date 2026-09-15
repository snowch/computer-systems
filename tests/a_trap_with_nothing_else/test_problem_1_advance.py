"""Checks Problem 4.1 by assembling the reader's instruction and measuring it.

Nothing about the answer is stored here. The instruction is assembled with the same toolchain the
chapter uses and its length read out of the object file, so the check is against the assembler
rather than against a list somebody wrote down.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from tests.a_trap_with_nothing_else.problem_1_advance import (
    AN_INSTRUCTION_THAT_BREAKS_IT,
    ITS_LENGTH_IN_BYTES,
    WHAT_THE_FOUR_IS,
)

AS = "riscv64-linux-gnu-as"
OBJDUMP = "riscv64-linux-gnu-objdump"


def assemble_one(instruction: str, directory) -> int:
    """Assemble one instruction and return how many bytes it took."""
    source = directory / "one.s"
    source.write_text(f"    .text\n    .globl probe\nprobe:\n    {instruction}\n")
    obj = directory / "one.o"
    subprocess.run(
        [AS, "-march=rv64gc", str(source), "-o", str(obj)],
        check=True,
        capture_output=True,
        text=True,
    )
    # The size of .text, from the section header. Counting instructions out of a disassembly
    # listing means parsing its layout; the section header is a number the assembler wrote.
    headers = subprocess.run(
        [OBJDUMP, "-h", str(obj)], check=True, capture_output=True, text=True
    ).stdout
    for line in headers.splitlines():
        fields = line.split()
        if len(fields) > 2 and fields[1] == ".text":
            return int(fields[2], 16)
    raise AssertionError("no .text section in the assembled object")


@pytest.mark.skipif(shutil.which(AS) is None, reason=f"needs {AS}")
def test_the_toolchain_can_tell_a_short_instruction_from_a_long_one(tmp_path):
    """Scaffolding: the measurement the problem rests on works at all.

    If the assembler here only ever produced four-byte instructions the problem would be
    unanswerable, and the reader would be stuck on a question with no right answer.
    """
    # Note what the assembler does unasked: with the compressed extension enabled it shortens
    # `addi a0, a0, 1` by itself. An immediate too large for the short form keeps four bytes.
    assert assemble_one("addi a0, a0, 2000", tmp_path) == 4
    assert assemble_one("addi a0, a0, 1", tmp_path) == 2


@pytest.mark.problem
def test_the_reader_named_what_the_four_is():
    assert WHAT_THE_FOUR_IS.strip(), "Problem 4.1: WHAT_THE_FOUR_IS is still empty"


@pytest.mark.problem
@pytest.mark.skipif(shutil.which(AS) is None, reason=f"needs {AS}")
def test_the_instruction_really_is_not_four_bytes(tmp_path):
    assert AN_INSTRUCTION_THAT_BREAKS_IT.strip(), (
        "Problem 4.1: AN_INSTRUCTION_THAT_BREAKS_IT is still empty"
    )
    measured = assemble_one(AN_INSTRUCTION_THAT_BREAKS_IT, tmp_path)
    assert measured != 4, (
        f"{AN_INSTRUCTION_THAT_BREAKS_IT!r} assembles to {measured} bytes, so advancing mepc by "
        "four would resume in exactly the right place — this is not a case that breaks it"
    )
    assert measured == ITS_LENGTH_IN_BYTES, (
        f"you said {ITS_LENGTH_IN_BYTES} bytes; the assembler says {measured}"
    )
