"""Compile the reader's console model and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

CONSOLE = ROOT / "tests" / "interrupts_and_drivers" / "console.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

BUF = 128
UNDECIDABLE = (1 << 64) - 1


def build(build_dir: Path) -> Path:
    return compile_program([CONSOLE], build_dir / "ch16console", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"lost": {}, "interrupts": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["lost", index, count]:
                # Keyed by which command it answered: one of the cases is the empty string.
                out["lost"][int(index)] = int(count)
            case ["interrupts", completions, per, count]:
                out["interrupts"][(int(completions), int(per))] = int(count)
    return out
