"""Checks Problem 4.2 by compiling each function and reading its prologue.

Both facts come out of the disassembly: a frame is a prologue that moves the stack pointer, and
saving the return address is a store of `ra`. Nothing is stored here, so a compiler that decides
differently moves the answers rather than failing every reader.
"""

from __future__ import annotations

import re

import pytest

from bench.disasm import disassemble
from bench.run_disasm import target_for
from tests.ch04.problem_2_frames import ANSWERS, FUNCTIONS

_MOVES_SP = re.compile(r"addi\s+sp,sp,-\d+")
_SAVES_RA = re.compile(r"\bsd\s+ra,")


@pytest.fixture(scope="module")
def observed(tmp_path_factory) -> dict[str, tuple[bool, bool]]:
    directory = tmp_path_factory.mktemp("frames")
    target = target_for("riscv64")
    out: dict[str, tuple[bool, bool]] = {}
    for name, source in FUNCTIONS.items():
        path = directory / f"{name}.c"
        path.write_text(source + "\n")
        text = disassemble([str(path)], "f", target, includes=[], build_dir=directory).text
        out[name] = (bool(_MOVES_SP.search(text)), bool(_SAVES_RA.search(text)))
    return out


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(FUNCTIONS))
def test_the_reader_predicted_the_prologue(name: str, observed):
    assert ANSWERS, "Problem 4.2: ANSWERS is still empty"
    assert name in ANSWERS, f"no answer for {name!r}"
    frame, saved = observed[name]
    assert ANSWERS[name] == (frame, saved), (
        f"{name}: you said {ANSWERS[name]}; the compiler produced "
        f"(frame={frame}, saves_ra={saved}) for\n  {FUNCTIONS[name]}"
    )


def test_the_four_are_not_all_the_same(observed):
    """Scaffolding: four functions with identical prologues would be a problem with no signal."""
    assert len(set(observed.values())) > 1, observed
