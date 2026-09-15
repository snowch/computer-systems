"""Compile the reader's locking code and ask it questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

LOCKING = ROOT / "tests" / "ch12" / "locking.c"

#: Threads need -pthread, which the book's portable flags have no reason to carry.
NATIVE = HostTarget(name="native-other", cc="cc", flags=(*PORTABLE_FLAGS, "-pthread"))


def build(build_dir: Path) -> Path:
    return compile_program([LOCKING], build_dir / "ch12locking", NATIVE).path


def ask(program: Path, commands: list[str], timeout: float = 120.0) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True, timeout=timeout
    ).stdout
    out: dict = {"hammer": [], "reorder": {}, "conflict": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["hammer", expected, got]:
                out["hammer"].append((int(expected), int(got)))
            case ["reorder", case, verdict]:
                out["reorder"][case] = int(verdict)
            case ["conflict", first, second, verdict]:
                out["conflict"][(first, second)] = int(verdict)
    return out
