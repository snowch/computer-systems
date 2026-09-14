"""Compile the reader's measurement code and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

MEASURING = ROOT / "tests" / "ch14" / "measuring.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


def build(build_dir: Path) -> Path:
    return compile_program([MEASURING], build_dir / "ch14measuring", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"summary": {}, "repetitions": {}, "warmup": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["summary", index, minimum, median, p90, mean]:
                out["summary"][int(index)] = tuple(int(v) for v in (minimum, median, p90, mean))
            case ["repetitions", case, value]:
                out["repetitions"][case] = int(value)
            case ["warmup", index, value]:
                out["warmup"][int(index)] = int(value)
    return out
