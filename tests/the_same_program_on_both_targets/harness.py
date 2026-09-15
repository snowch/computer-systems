"""Compile the reader's crossing model and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

CROSSING = ROOT / "tests" / "the_same_program_on_both_targets" / "crossing.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

#: name -> (emulated, kernel, instruction set), mirroring the table in crossing.c.
CONFIGS = {
    "A": (1, "x", "r"),
    "B": (1, "l", "r"),
    "C": (0, "l", "r"),
    "D": (0, "l", "a"),
    "E": (0, "x", "r"),
    "F": (1, "l", "a"),
}


def build(build_dir: Path) -> Path:
    return compile_program([CROSSING], build_dir / "ch20crossing", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"isolates": {}, "pair": {}, "transfers": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["isolates", case, verdict]:
                out["isolates"][case] = verdict
            case ["pair", case, found, other]:
                out["pair"][case] = (int(found), other)
            case ["transfers", what, verdict]:
                out["transfers"][what] = int(verdict)
    return out
