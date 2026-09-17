"""Checks Problem 1.3 by compiling the reader's function and reading what came out.

Two assertions, and both are needed. That it computes the right answer is the easy half; that the
compiler still emitted a loop is the half the problem is about, and it can only be checked by
looking at the instructions. This is the first time in the book a test reads machine code, and it
uses the same module the chapters' listings come from.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from bench.disasm import disassemble
from bench.run_disasm import target_for
from tests.what_a_computer_does_with_a_program.problem_3_unfold import UNFOLDABLE_SUM

SPAN = 64
EXPECTED = SPAN * (SPAN - 1) // 2

#: A branch to an address lower than its own: the shape of every loop, on every architecture the
#: book compiles for. Read off the offsets objdump prints rather than the mnemonic, because the
#: two instruction sets do not agree on what a branch is called.
_BRANCH = re.compile(r"^\s+([0-9a-f]+):\t\S*\s+.*?\b([0-9a-f]+)\s+<", re.MULTILINE)


def _has_backward_branch(listing: str) -> bool:
    return any(int(target, 16) <= int(here, 16) for here, target in _BRANCH.findall(listing))


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    if not shutil.which("riscv64-linux-gnu-gcc"):
        pytest.skip("riscv64-linux-gnu-gcc is not installed (see the setup chapter)")
    directory = tmp_path_factory.mktemp("unfold")
    (directory / "reader.c").write_text(UNFOLDABLE_SUM)
    return directory


@pytest.mark.problem
def test_the_reader_function_computes_the_sum(built):
    """It has to be right before it has to be interesting."""
    harness = built / "main.c"
    harness.write_text(
        "#include <stdio.h>\nunsigned long reader_sum(unsigned long);\n"
        f'int main(void){{ printf("%lu\\n", reader_sum({SPAN})); return 0; }}\n'
    )
    binary = built / "reader"
    subprocess.run(
        [
            "riscv64-linux-gnu-gcc",
            "-O2",
            "-march=rv64gc",
            "-mabi=lp64d",
            "-static",
            str(built / "reader.c"),
            str(harness),
            "-o",
            str(binary),
        ],
        check=True,
        capture_output=True,
    )
    runner = shutil.which("qemu-riscv64-static") or shutil.which("qemu-riscv64")
    if not runner:
        pytest.skip("no user-mode QEMU to run RV64 with (see the setup chapter)")
    out = subprocess.run([runner, str(binary)], capture_output=True, text=True, check=True).stdout
    assert out.strip() == str(EXPECTED), f"reader_sum({SPAN}) should be {EXPECTED}"


@pytest.mark.problem
def test_the_compiler_still_emitted_a_loop(built):
    """The point of the problem: a correct answer the compiler folded away does not count."""
    target = target_for("riscv64")
    listing = disassemble(
        [str(built / "reader.c")], "reader_sum", target, includes=[], build_dir=built
    )
    assert _has_backward_branch(listing.text), (
        "reader_sum has no backward branch, so no loop runs: the compiler worked the answer out "
        f"at compile time. What it emitted was:\n{listing.text}"
    )


def test_the_detector_knows_a_loop_from_a_constant(built):
    """Scaffolding: the check above is only worth having if it can tell the two apart.

    Both cases come from the book's own example file, which the chapter also prints — one of them
    is a loop and the other is two instructions, and the detector must agree.
    """
    target = target_for("riscv64")
    folded = disassemble(
        ["sysfs/lib/stages.c"], "sysfs_sum_folded", target, includes=["sysfs/include"]
    )
    counted = disassemble(
        ["sysfs/lib/stages.c"], "sysfs_sum_counted", target, includes=["sysfs/include"]
    )
    assert not _has_backward_branch(folded.text), folded.text
    assert _has_backward_branch(counted.text), counted.text
