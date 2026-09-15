"""Compile the reader's hierarchy analysis and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

HIERARCHY = ROOT / "tests" / "ch22" / "hierarchy.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


def build(build_dir: Path) -> Path:
    return compile_program([HIERARCHY], build_dir / "ch22hierarchy", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"steps": {}, "line": {}, "lines": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["steps", index, _count, *found]:
                out["steps"][int(index)] = [int(v) for v in found]
            case ["line", index, value]:
                out["line"][int(index)] = int(value)
            case ["lines", elements, value]:
                out["lines"][int(elements)] = int(value)
    return out


def curve(points: list[tuple[int, int]]) -> tuple[str, str]:
    return ".".join(str(x) for x, _ in points), ".".join(str(y) for _, y in points)
