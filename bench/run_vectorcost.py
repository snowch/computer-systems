#!/usr/bin/env python3
"""Chapter 23's measurement: what widening bought, beside the most it could possibly have bought.

    python3 -m bench.run_vectorcost          # on the board only
    python3 -m bench.run_vectorcost --check  # re-run and compare; write nothing

One source built twice — at the book's own level, and at the one where this compiler starts
widening — with everything else about the two builds identical. The speedup is the ratio between
the runs; the bound is what the register width allows for that element size; the achieved
percentage is the ratio between those, and it is the number the chapter asks for instead of a
speedup.

Deliberately not clamped. A loop that comes out above its arithmetic bound has had something other
than its width change, and ch28 says that is a signal to look again rather than a triumph. A
runner that quietly pinned it to a hundred would turn the one informative result into a success.

The census in `bench.run_vectors` already establishes which of these five the compiler widens and
at what flags, from the disassembly. This runner does not re-derive that: it measures, and the
chapter puts the two side by side.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/vectorcost.c"
LIBRARY = "sysfs/lib/vectors.c"
HEADER = "sysfs/include/sysfs/vectors.h"
FIGURE = "vectors-speedup"

#: The width of one vector register on this book's `host` architecture, in bits. NEON is fixed at
#: 128; a scalable extension would make this a property of the running machine instead, which is
#: the limitation ch28's own last section names.
VECTOR_BITS = 128

#: The two builds. The first is what a reader building this code gets.
BUILDS = {"scalar": [], "widened": ["-O3"]}


class VectorCostError(RuntimeError):
    """The two builds stopped being two builds of one program."""


def parse(text: str) -> dict[str, dict[str, int]]:
    loops: dict[str, dict[str, int]] = {}
    complete = False
    for line in text.splitlines():
        match line.split():
            case ["loop", name, "total_ns", total, "element_bits", bits]:
                loops[name] = {"total_ns": int(total), "element_bits": int(bits)}
            case ["end", "vectorcost"]:
                complete = True
    if not complete or not loops:
        raise VectorCostError(f"vectorcost did not finish:\n{text[-2000:]}")
    return loops


def capture() -> dict[str, Any]:
    require_board(FIGURE)

    runs = {
        build: parse(
            timed_run([WORKLOAD, LIBRARY], f"vectorcost-{build}", extra_flags=flags or None)
        )
        for build, flags in BUILDS.items()
    }

    scalar, widened = runs["scalar"], runs["widened"]
    if set(scalar) != set(widened):
        raise VectorCostError("the two builds measured different loops")

    loops: dict[str, Any] = {}
    for name, base in scalar.items():
        fast = widened[name]
        if not fast["total_ns"]:
            raise VectorCostError(f"{name} measured zero in the widened build; the loop is gone")
        bound = VECTOR_BITS / base["element_bits"]
        speedup = base["total_ns"] / fast["total_ns"]
        loops[name] = {
            "scalar_ns": base["total_ns"],
            "widened_ns": fast["total_ns"],
            "speedup": round(speedup, 2),
            "bound": round(bound, 2),
            # Not clamped. See the module docstring.
            "achieved_pct": round(100 * speedup / bound, 1),
        }

    return stamp_timing(
        "vectors-host",
        {"loops": loops, "vector_bits": VECTOR_BITS, "governor": governor()},
        ["bench/run_vectorcost.py", WORKLOAD, LIBRARY, HEADER],
        note="one source built twice, differing only in the optimisation level",
        workload="sysfs/bench/vectorcost.c",
    )


#: The shape this runner produces. See `bench/run_measuring.py` for why it is here.
SHAPE = {
    "loops": {
        "sysfs_vec_scale": {
            "scalar_ns": 222,
            "widened_ns": 111,
            "speedup": 2.22,
            "bound": 4.0,
            "achieved_pct": 55.5,
        },
        "sysfs_vec_running": {
            "scalar_ns": 111,
            "widened_ns": 111,
            "speedup": 1.0,
            "bound": 4.0,
            "achieved_pct": 25.0,
        },
    },
    "vector_bits": 128,
    "governor": "performance",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and compare; write nothing")
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
        print(f"{payload['name']}: unchanged")
        return 0
    print(f"{payload['name']}: the measurement has moved\n")
    for difference in differences:
        print(f"  {difference}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
