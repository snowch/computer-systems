"""Compile the reader's page-table code and ask it questions.

Shared by all three of chapter 7's problems, which are one program: 7.1 builds a page table, 7.2
follows it, and 7.3 says where following it stops. They are graded separately but they run in the
same arena, because a page table you cannot walk is not evidence of anything.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.run_pagetable import MODEL, MODEL_LIB, parse_model
from bench.stamp import ROOT

WALK = ROOT / "tests" / "ch14" / "walk.c"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)

PAGE = 4096


def build(build_dir: Path) -> Path:
    return compile_program([WALK], build_dir / "ch14walk", NATIVE).path


def ask(program: Path, commands: list[str]) -> dict:
    """Run one session and read back what it said. One process, one arena, one page table."""
    printed = subprocess.run(
        [str(program), *commands], capture_output=True, text=True, check=True
    ).stdout
    out: dict = {"translate": {}, "missing": {}, "map": {}, "allocated": None}
    for line in printed.splitlines():
        parts = line.split()
        match parts:
            case ["map", va, status]:
                out["map"][int(va, 16)] = int(status)
            case ["translate", va, "fault"]:
                out["translate"][int(va, 16)] = None
            case ["translate", va, pa]:
                out["translate"][int(va, 16)] = int(pa, 16)
            case ["missing", va, level]:
                out["missing"][int(va, 16)] = int(level)
            case ["allocated", count]:
                out["allocated"] = int(count)
    if out["allocated"] is None:
        raise AssertionError(f"the harness did not finish:\n{printed}")
    return out


def maps(pairs: list[tuple[int, int]]) -> list[str]:
    return [f"m{va:#x},{pa:#x}" for va, pa in pairs]


def run_of(start: int, pages: int, physical: int) -> list[tuple[int, int]]:
    """One run of consecutive virtual pages, landing on consecutive physical ones."""
    return [(start + i * PAGE, physical + i * PAGE) for i in range(pages)]


def tables_needed(build_dir: Path, runs: list[tuple[int, int]]) -> int:
    """What chapter 7's model says these runs cost, derived from the addresses alone.

    This is the oracle for problem 7.1, and it is not a second implementation of the answer: the
    model counts page-table pages from a list of address ranges and has no idea how to build one.
    """
    model = compile_program(
        [MODEL, MODEL_LIB], build_dir / "ch14model", NATIVE, includes=["sysfs/include"]
    ).path
    arguments = [f"{start:#x}:{pages}" for start, pages in runs]
    printed = subprocess.run(
        [str(model), "tables", *arguments], capture_output=True, text=True, check=True
    ).stdout
    return parse_model(printed)["total"]
