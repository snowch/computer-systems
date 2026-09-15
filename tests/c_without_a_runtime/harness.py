"""Compile the reader's kernel-C exercises and ask them questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

RUNTIME = ROOT / "tests" / "c_without_a_runtime" / "runtime.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

POOL = 8

R_CANNOT_FAIL, R_NULL, R_NEGATIVE, R_UNREPORTABLE = range(4)
MODE_NAMES = {
    R_CANNOT_FAIL: "cannot fail",
    R_NULL: "a null pointer",
    R_NEGATIVE: "a negative status",
    R_UNREPORTABLE: "it cannot say",
}


def build(build_dir: Path) -> Path:
    return compile_program([RUNTIME], build_dir / "ch02runtime", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"pool": {}, "failure": {}, "reads": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["pool", index, *values]:
                out["pool"][int(index)] = [int(v) for v in values]
            case [("failure" | "reads") as what, index, value]:
                out[what][int(index)] = int(value)
    return out
