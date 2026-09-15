"""Compile the reader's predictor model and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

PREDICTOR = ROOT / "tests" / "ch19" / "predictor.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


def build(build_dir: Path) -> Path:
    return compile_program([PREDICTOR], build_dir / "ch19predictor", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"path": {}, "mispredicts": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["path", case, value]:
                out["path"][case] = int(value)
            case ["mispredicts", outcomes, value]:
                out["mispredicts"][outcomes] = int(value)
    return out
