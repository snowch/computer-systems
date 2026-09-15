"""Checks Problem 5.3 by assembling the instruction and refusing the chapter's own answer."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from bench.stamp import load_result
from tests.interrupts_and_privilege.problem_3_another_refusal import (
    ITS_CAUSE,
    THE_INSTRUCTION,
    WHY,
)

AS = "riscv64-linux-gnu-as"


def test_the_chapters_refusal_was_cause_two():
    """Scaffolding: the answer the reader may not reuse is the one the chapter measured."""
    assert load_result("privilege-bare")["summary"]["refusal_code"] == 2


@pytest.mark.problem
@pytest.mark.skipif(shutil.which(AS) is None, reason=f"needs {AS}")
def test_the_instruction_assembles_and_is_not_the_chapters(tmp_path):
    assert THE_INSTRUCTION.strip(), "Problem 5.3: THE_INSTRUCTION is still empty"
    assert "mhartid" not in THE_INSTRUCTION, "that is the one the chapter already used"

    source = tmp_path / "probe.s"
    source.write_text(f"    .text\nprobe:\n    {THE_INSTRUCTION}\n")
    result = subprocess.run(
        [AS, "-march=rv64g", str(source), "-o", str(tmp_path / "probe.o")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"that does not assemble:\n{result.stderr}"


@pytest.mark.problem
def test_the_cause_differs_from_the_chapters():
    assert ITS_CAUSE != 2, (
        "cause 2 is illegal instruction, which is what the chapter already showed — the problem "
        "asks for a refusal of a different kind"
    )
    assert ITS_CAUSE > 0, "Problem 5.3: ITS_CAUSE is still unset"
    assert len(WHY.split()) >= 4, "Problem 5.3: WHY wants a phrase"
