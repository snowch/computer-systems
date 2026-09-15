"""Compile the reader's profile reader and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

PROFILER = ROOT / "tests" / "ch22" / "profiler.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


def build(build_dir: Path) -> Path:
    return compile_program([PROFILER], build_dir / "ch22profiler", NATIVE).path


def tree_command(nodes: list[tuple[int, int]]) -> str:
    """`t` takes parent:exclusive pairs, in an order where every parent precedes its children."""
    return "t" + ".".join(f"{parent}:{exclusive}" for parent, exclusive in nodes)


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"inclusive": {}, "needed": {}, "aliased": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["inclusive", index, *values]:
                out["inclusive"][int(index)] = [int(v) for v in values]
            case [("needed" | "aliased") as what, index, value]:
                out[what][int(index)] = int(value)
    return out
