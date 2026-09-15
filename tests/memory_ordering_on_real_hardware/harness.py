"""Compile the reader's sharing model and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

SHARING = ROOT / "tests" / "memory_ordering_on_real_hardware" / "sharing.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)
LINE = 64


def build(build_dir: Path) -> Path:
    return compile_program([SHARING], build_dir / "ch25sharing", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"pairs": {}, "speedup": {}, "spelling": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["pairs", index, value]:
                out["pairs"][int(index)] = int(value)
            case ["speedup", case, value]:
                out["speedup"][case] = int(value)
            case ["spelling", case, *words]:
                out["spelling"][case] = " ".join(words)
    return out
