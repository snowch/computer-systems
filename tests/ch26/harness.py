"""Compile the reader's cost model and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

OSCOST = ROOT / "tests" / "ch26" / "oscost.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

O_NONE, O_MINOR, O_MAJOR, O_FATAL = 0, 1, 2, 3
KIND_NAMES = {O_NONE: "none", O_MINOR: "minor", O_MAJOR: "major", O_FATAL: "fatal"}


def build(build_dir: Path) -> Path:
    return compile_program([OSCOST], build_dir / "ch26oscost", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    """Run the model over `commands` and key every answer by the command's position.

    Keying by position rather than by the text of the command is deliberate: two cases can have
    identical arguments, and an empty one prints a blank field that no split() survives.
    """
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"reported": {}, "bound": {}, "fault": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case [("reported" | "bound" | "fault") as what, index, value]:
                out[what][int(index)] = int(value)
    return out
