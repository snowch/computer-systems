"""Compile the reader's C-reading exercises and ask them questions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT

DECLARATIONS = ROOT / "tests" / "reading_c" / "declarations.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

D_VALUE, D_POINTER, D_ARRAY, D_ARRAY_PTR, D_PTR_ARRAY, D_FUNC_PTR, D_FUNC = range(7)
KIND_NAMES = {
    D_VALUE: "a plain object",
    D_POINTER: "a pointer",
    D_ARRAY: "an array",
    D_ARRAY_PTR: "an array of pointers",
    D_PTR_ARRAY: "a pointer to an array",
    D_FUNC_PTR: "a pointer to a function",
    D_FUNC: "a function",
}


def build(build_dir: Path) -> Path:
    return compile_program([DECLARATIONS], build_dir / "ch01declarations", NATIVE).path


def checksum(data: bytes) -> int:
    """The harness's own sum over the copied bytes, mirrored here so the key is derived."""
    total = 0
    for byte in data:
        total = (total * 31 + byte) % (1 << 64)
    return total


def ask(program: Path, commands: list[str]) -> dict:
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"declare": {}, "length": {}, "copy": {}, "compare": {}, "round": {}}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case [("declare" | "length" | "compare") as what, index, value]:
                out[what][int(index)] = int(value)
            case ["copy", index, total, sentinel]:
                out["copy"][int(index)] = (int(total), int(sentinel))
            case ["round", index, down, up]:
                out["round"][int(index)] = (int(down), int(up))
    return out
