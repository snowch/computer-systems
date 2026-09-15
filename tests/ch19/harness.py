"""Compile the reader's file-system model and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

FILESYSTEM = ROOT / "tests" / "ch19" / "filesystem.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

NOTHING, REPLAY = 0, 1


def build(build_dir: Path) -> Path:
    return compile_program([FILESYSTEM], build_dir / "ch19fs", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"writes": {}, "crash": {}, "safe": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["writes", blocks, count]:
                out["writes"][int(blocks)] = int(count)
            case ["crash", stage, verdict]:
                out["crash"][int(stage)] = int(verdict)
            case ["safe", order, verdict]:
                out["safe"][order] = int(verdict)
    return out
