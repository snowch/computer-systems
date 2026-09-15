"""Compile the reader's scheduling code and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

SCHEDULING = ROOT / "tests" / "ch13" / "scheduling.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


def build(build_dir: Path) -> Path:
    return compile_program([SCHEDULING], build_dir / "ch13sched", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"save": {}, "lost": {}, "order": []}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["save", case, verdict]:
                out["save"][case] = int(verdict)
            case ["lost", index, verdict]:
                out["lost"][int(index)] = int(verdict)
            case ["order", _policy, *slots]:
                out["order"].append([int(s) for s in slots])
    return out
