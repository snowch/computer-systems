"""Checks Problem 4.1 by compiling both and comparing instruction for instruction.

The target is compiled from a source the reader never sees, printed as a listing, and the
reader's attempt is compiled the same way. Offsets are stripped before comparing: two functions
built separately land at different addresses and that is not a difference worth failing over.
"""

from __future__ import annotations

import pytest

from bench.disasm import disassemble
from bench.run_disasm import target_for
from tests.ch04.problem_1_reconstruct import RECONSTRUCTION, SIGNATURE

#: The function the reader is reconstructing. Kept here rather than in the problem file so that
#: reading the problem does not answer it — and chosen so that the obvious C is not the right C.
_TARGET = """
long reader_target(long a, long b) {
  long scaled = a * 8;
  return scaled - b + (a >> 3);
}
"""


def _body(text: str) -> list[str]:
    return [line.split(":\t", 1)[1].strip() for line in text.splitlines() if ":\t" in line]


@pytest.fixture(scope="module")
def target_listing(tmp_path_factory) -> str:
    directory = tmp_path_factory.mktemp("reconstruct_target")
    (directory / "target.c").write_text(_TARGET)
    return disassemble(
        [str(directory / "target.c")],
        "reader_target",
        target_for("riscv64"),
        includes=[],
        build_dir=directory,
    ).text


@pytest.mark.problem
def test_the_reconstruction_compiles_to_the_same_instructions(tmp_path, target_listing):
    assert SIGNATURE in RECONSTRUCTION, "keep the signature the problem gives you"
    (tmp_path / "reader.c").write_text(RECONSTRUCTION)
    mine = disassemble(
        [str(tmp_path / "reader.c")],
        "reader_target",
        target_for("riscv64"),
        includes=[],
        build_dir=tmp_path,
    ).text
    assert _body(mine) == _body(target_listing), (
        "not the same instructions.\n\nYou are aiming for:\n"
        + target_listing
        + "\n\nYours compiled to:\n"
        + mine
    )


def test_the_target_is_not_trivially_guessable(target_listing):
    """Scaffolding: a target that compiles to two instructions is a problem with no content."""
    assert len(_body(target_listing)) >= 4, target_listing
