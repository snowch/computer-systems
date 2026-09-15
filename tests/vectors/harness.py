"""Compile the reader's lane arithmetic and ask it questions."""

from __future__ import annotations

import struct
import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

LANES = ROOT / "tests" / "vectors" / "lanes.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


def build(build_dir: Path) -> Path:
    return compile_program([LANES], build_dir / "ch28lanes", NATIVE).path


def f32(value: float) -> float:
    """Round a Python float to the nearest float, the way the C does."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def add32(a: float, b: float) -> float:
    """One single-precision addition.

    Exact: the sum of two floats is always representable in a double, so the only rounding is the
    one back down — which is the rounding the problem is about.
    """
    return f32(f32(a) + f32(b))


def bits(value: float) -> str:
    return f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"speedup": {}, "bound": {}, "sum": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case [("speedup" | "bound") as what, index, value]:
                out[what][int(index)] = int(value)
            case ["sum", index, sequential, lanewise]:
                out["sum"][int(index)] = (sequential, lanewise)
    return out
