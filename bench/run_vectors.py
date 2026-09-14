#!/usr/bin/env python3
"""Chapter 21's evidence: five loops, two optimisation levels, and which of them got wider.

    python3 -m bench.run_vectors           # capture and stamp
    python3 -m bench.run_vectors --check   # re-capture and diff; write nothing

Separate from ``bench.run_disasm`` for one reason: every other listing in the book is compiled at
the book's own flags, and this chapter's question cannot be asked at one optimisation level. "When
will the compiler do it for me?" has an answer that begins "not at the level you are probably
using", and showing that needs both.

Three results come out. Two are ordinary listings, one per level, so the chapter can print what
the compiler emitted; the third is a census counting how many of each function's instructions
operate on vector registers, which is what turns five listings into one table.

Counting vector instructions from their operands is a heuristic, and it is stated as one rather
than dressed up. The census refuses to stamp a result in which the loop the chapter calls
impossible to widen has acquired vector instructions — and that refusal has already earned its
place: the first version of the counting rule tripped it, correctly, on an instruction that names
a vector register while doing scalar work.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from bench.disasm import code_flags, disassemble
from bench.measure import HostTarget, ToolchainMissingError, flags_for
from bench.run_disasm import CROSS_PREFIX, target_for
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

ARCH = "aarch64"
SOURCE = "sysfs/lib/vectors.c"
HEADER = "sysfs/include/sysfs/vectors.h"

SYMBOLS = (
    "sysfs_vec_scale",
    "sysfs_vec_sum_i32",
    "sysfs_vec_sum_f32",
    "sysfs_vec_gather",
    "sysfs_vec_running",
)

#: The three builds the chapter compares, and the flags that distinguish them.
#:
#: `-O2` is the book's own level everywhere else, so it is what a reader building this code will
#: get. `-O3` is where this compiler starts paying for vectorisation. `-ffast-math` is the third
#: because one of these loops is refused for a reason that is not a limitation of the compiler at
#: all — it would have to change the program's answer — and the only way to show that is to
#: give it permission and watch what happens.
LEVELS = {"o2": (), "o3": ("-O3",), "o3fast": ("-O3", "-ffast-math")}

#: An operand naming a *full-width* vector register — a `q` register, or one of the four
#: 128-bit arrangement specifiers.
#:
#: The width matters, and finding out why is the reason this file has a guard in it. A first
#: attempt counted anything naming a `v` register, and the loop the chapter calls impossible to
#: widen came back with one: `movi v0.2s, #0x0`, which is how this compiler makes a floating-point
#: zero. The half-width forms are used for scalar work, so grepping for vector registers does not
#: answer "did this loop vectorise" — it answers "is there a float in here".
VECTOR_OPERAND = re.compile(r"\b(?:q\d+|v\d+\.(?:16b|8h|4s|2d))\b")

#: The loop whose dependence chain no width can help. If this one ever comes back with vector
#: instructions in it, either the compiler has found something the chapter says is impossible or
#: the counting heuristic has broken, and both want a human.
NEVER_WIDENS = "sysfs_vec_running"


class VectorCensusError(RuntimeError):
    """The evidence stopped supporting what the chapter says about it."""


def level_target(level: str) -> HostTarget:
    """The book's own aarch64 listing target, with this level's flags appended.

    Appended rather than substituted: ``-O3`` after ``-O2`` is what a reader would type, and it
    keeps every other flag identical so the only difference between the two results is the one
    being studied.
    """
    base = target_for(ARCH)
    return HostTarget(
        name=f"{base.name}-{level}",
        cc=base.cc,
        flags=(*code_flags(flags_for(ARCH)), *LEVELS[level]),
        why=f"compiled for {ARCH} at {level}; never executed",
    )


def capture_listings(level: str) -> dict[str, Any]:
    target = level_target(level)
    listings, toolchain = {}, {}
    for symbol in SYMBOLS:
        got = disassemble([SOURCE], symbol, target, includes=["sysfs/include"])
        if got.arch != ARCH:
            raise RuntimeError(f"asked for {ARCH} and objdump read {got.arch}")
        listings[symbol] = got.as_summary()
        toolchain = dict(got.toolchain)
    toolchain["objdump"] = toolchain["objdump"].split(" --disassemble=")[0] + " --disassemble=<fn>"

    return build_result(
        name=f"vectors-{level}",
        target="host",
        kind="listing",
        summary={"source": SOURCE, "listings": listings},
        code_sources=["bench/run_vectors.py", "bench/disasm.py", SOURCE, HEADER],
        toolchain=toolchain | {"execution": "none — compiled to an object file and disassembled"},
        machine=describe_toolchain(ARCH),
        conditions={
            "note": "what the compiler chose at this level, not what the choice cost",
            "compiler": compiler_version(target.cc),
        },
    )


def count_vector_instructions(text: str) -> int:
    """Instructions whose operands name a vector register."""
    return sum(1 for line in text.splitlines() if VECTOR_OPERAND.search(line))


def census(levels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    loops: dict[str, Any] = {}
    for symbol in SYMBOLS:
        loops[symbol] = {}
        for level, payload in levels.items():
            entry = payload["summary"]["listings"][symbol]
            loops[symbol][level] = {
                "instructions": entry["instructions"],
                "vector": count_vector_instructions(entry["text"]),
            }

    widened = [s for s in SYMBOLS if loops[s]["o3"]["vector"] > loops[s]["o2"]["vector"]]
    widened_by_permission = [
        s for s in SYMBOLS if loops[s]["o3fast"]["vector"] > loops[s]["o3"]["vector"]
    ]
    if not widened:
        raise VectorCensusError(
            "no loop gained vector instructions at -O3. The chapter's whole comparison is between "
            "a level that widens some of these and one that widens none; with this compiler it "
            "has nothing to compare."
        )
    if not widened_by_permission:
        raise VectorCensusError(
            "no loop widened when -ffast-math allowed the answer to change. The chapter's second "
            "finding is that one of these is refused for a reason that is not the compiler's "
            "limitation, and without this it has no evidence for it."
        )
    if loops[NEVER_WIDENS]["o3fast"]["vector"]:
        raise VectorCensusError(
            f"{NEVER_WIDENS} came back with vector instructions. The chapter says a "
            "loop-carried dependence cannot be widened; either that is now wrong here, or the "
            "instruction-counting heuristic is. Read the listing before changing the number."
        )

    return build_result(
        name="vectors-census",
        target="host",
        kind="artefact",
        summary={
            "loops": loops,
            "widened": widened,
            "widened_by_permission": widened_by_permission,
            "levels": sorted(levels),
        },
        code_sources=["bench/run_vectors.py", SOURCE, HEADER],
        toolchain={
            "cc": f"{CROSS_PREFIX[ARCH]}gcc",
            "flags": "the book's aarch64 listing flags, then with -O3, then with -O3 -ffast-math",
            "execution": "none — counted from the disassembly, which is why it needs no machine",
        },
        machine=describe_toolchain(ARCH),
        conditions={
            "note": "a vector instruction is counted by its operands naming a vector register",
            "why": "a heuristic, guarded by refusing a census where the unvectorisable loop widens",
        },
    )


def compare(payload: dict[str, Any], what: str) -> int:
    try:
        committed = load_result(payload["name"])
    except FileNotFoundError:
        print(f"{payload['name']}: nothing committed to compare against")
        return 1
    differences = measurement_differences(committed, payload)
    if not differences:
        print(f"{payload['name']}: unchanged — {what}")
        return 0
    print(f"{payload['name']}: has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_vectors\n  python3 scripts/render-figures.py"
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-capture and diff; write nothing")
    args = parser.parse_args(argv)

    try:
        levels = {level: capture_listings(level) for level in LEVELS}
    except ToolchainMissingError as exc:
        print(f"run_vectors: {exc}", file=sys.stderr)
        return 1
    payloads = [*levels.values(), census(levels)]

    status = 0
    for payload in payloads:
        if args.check:
            status |= compare(payload, "the compiler still makes the same of ch21's five loops")
        else:
            path = write_result(payload)
            print(f"wrote {Path(path).relative_to(ROOT)}")
    return status


if __name__ == "__main__":
    sys.exit(main())
