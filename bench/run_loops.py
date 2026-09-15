#!/usr/bin/env python3
"""Chapter 16's artefact: what the compiler does to five versions of one loop.

    python3 -m bench.run_loops           # compile each variant at each level and stamp the counts
    python3 -m bench.run_loops --check   # re-compile and compare; write nothing

Not a timing, and it does not need to be. The question ch23 asks first is *whether the source
change survived the compiler at all* — and that is answered by the instruction counts, which are
compiler output rather than machine behaviour, so CI regenerates them on every push exactly as it
does the listings.

What the surviving differences cost is a separate question, needs the board, and is `optimising-code-cost`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.disasm import disassemble
from bench.measure import HostTarget
from bench.run_disasm import flags_for, target_for
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

SOURCE = "sysfs/lib/loops.c"
HEADER = "sysfs/include/sysfs/loops.h"
ARCH = "aarch64"

VARIANTS = (
    "sysfs_loop_plain",
    "sysfs_loop_hoisted",
    "sysfs_loop_reduced",
    "sysfs_loop_unrolled",
    "sysfs_loop_everything",
)
LEVELS = ("-O0", "-O2", "-O3")


def measure(symbol: str, level: str) -> int:
    base = target_for(ARCH)
    flags = tuple(f for f in flags_for(ARCH) if not f.startswith("-O")) + (level,)
    target = HostTarget(name=f"loops-{ARCH}", cc=base.cc, flags=flags)
    return disassemble([SOURCE], symbol, target, includes=["sysfs/include"]).instructions


def capture() -> dict[str, Any]:
    counts = {level: {symbol: measure(symbol, level) for symbol in VARIANTS} for level in LEVELS}
    # How many distinct instruction counts the five variants have, at each level. One means the
    # compiler produced the same code for all five and every hand-optimisation was wasted effort.
    distinct = {level: len(set(counts[level].values())) for level in LEVELS}
    return build_result(
        name="loops-aarch64",
        target="host",
        kind="listing",
        summary={
            "source": SOURCE,
            "instructions": counts,
            "distinct_shapes": distinct,
            "listings": {
                symbol: {
                    "symbol": symbol,
                    "text": f"{symbol} at -O2: {counts['-O2'][symbol]} instructions",
                    "instructions": counts["-O2"][symbol],
                }
                for symbol in VARIANTS
            },
        },
        code_sources=["bench/run_loops.py", SOURCE, HEADER],
        toolchain={
            "cc": compiler_version(target_for(ARCH).cc),
            "flags": f"{' '.join(flags_for(ARCH))} at each of {' '.join(LEVELS)}",
            "execution": "none — compiled, not run",
        },
        machine=describe_toolchain(ARCH),
        conditions={
            "note": "instruction counts only; what the surviving differences cost needs the board",
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="re-compile and compare; write nothing"
    )
    args = parser.parse_args(argv)

    payload = capture()
    if not args.check:
        path = write_result(payload)
        print(f"wrote {Path(path).relative_to(ROOT)}")
        return 0
    try:
        committed = load_result(payload["name"])
    except FileNotFoundError:
        print(f"{payload['name']}: nothing committed to compare against")
        return 1
    differences = measurement_differences(committed, payload)
    if not differences:
        print(f"{payload['name']}: unchanged — the compiler still makes these of them")
        return 0
    print(f"{payload['name']}: the compiler's output has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print("\nRe-run and commit:\n  python3 -m bench.run_loops\n  python3 scripts/render-figures.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
