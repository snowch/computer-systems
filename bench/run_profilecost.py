#!/usr/bin/env python3
"""Chapter 22's measurements: where the samples landed, before and after, and on which instruction.

    python3 -m bench.run_profilecost          # on the board only, and needs perf to sample
    python3 -m bench.run_profilecost --check  # re-run and compare; write nothing

Two results from one program. `tally` runs one arrangement per invocation, because a process that
ran both would give one profile covering both — a fair description of neither.

The census in `bench.run_profile` wrote down what this program does before anybody timed it. This
runner is the other half of that method: the profile arrives afterwards, and the chapter is about
whether the two agree.

`skid-host` is the instruction-level view of the scattered loop, and the point of it is that the
sample does not land on the instruction that stalled. The runner does not try to correct for that
— correcting would be inventing a number — it records where the samples actually fell and the
chapter explains the gap.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

from bench.board import (
    NATIVE,
    governor,
    perf_annotate,
    perf_record,
    perf_report,
    require_board,
    require_perf_sampling,
    stamp_timing,
)
from bench.measure import compile_program
from bench.stamp import ROOT, load_result, measurement_differences, write_result

PROGRAM = "sysfs/tools/tally.c"
LIBRARY = "sysfs/lib/profiling.c"
HEADER = "sysfs/include/sysfs/profiling.h"
FIGURE = "ch27-profile and ch27-skid"

#: The loop ch27 reads instruction by instruction.
HOT = "sysfs_tally_scatter"

#: Below this share of samples a symbol is noise rather than a finding, and ch27's second problem
#: is the arithmetic for why.
FLOOR = 1.0


class ProfileError(RuntimeError):
    """The profile did not describe the program the chapter profiles."""


def build() -> Path:
    """Built with frame pointers and symbols, which a profile is useless without.

    `-fno-omit-frame-pointer` is not about this book's call graphs — it asks for none — but about
    perf being able to attribute a sample at all on a build the optimiser has rearranged.
    """
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    target = type(NATIVE)(
        name=f"{NATIVE.name}-profiled",
        cc=NATIVE.cc,
        flags=(*NATIVE.flags, "-fno-omit-frame-pointer"),
        trustworthy_for_timing=True,
        why=NATIVE.why,
    )
    return compile_program(
        [PROGRAM, LIBRARY], build_dir / "tally", target, includes=["sysfs/include"]
    ).path


def shares(rows: list[tuple[float, str]]) -> dict[str, float]:
    merged: dict[str, float] = {}
    for percent, symbol in rows:
        merged[symbol] = round(merged.get(symbol, 0.0) + percent, 2)
    return merged


def capture() -> list[dict[str, Any]]:
    require_board(FIGURE)
    require_perf_sampling(FIGURE)
    program = build()

    with tempfile.TemporaryDirectory() as scratch:
        before_file = Path(scratch) / "before.data"
        after_file = Path(scratch) / "after.data"
        perf_record(before_file, [str(program), "scatter"])
        perf_record(after_file, [str(program), "partitioned"])

        before = shares(perf_report(before_file))
        after = shares(perf_report(after_file))
        annotated = perf_annotate(before_file, HOT)

    if not before:
        raise ProfileError(
            "the profile of the scattered arrangement contains no samples. The program may have "
            "finished before the first one was taken; PROFILE_PASSES in tally.c is what to raise."
        )
    if HOT not in before:
        raise ProfileError(
            f"{HOT} does not appear in its own profile at all, which means the symbol was "
            f"inlined away or stripped. perf saw: {sorted(before)}"
        )
    if before[HOT] < FLOOR:
        raise ProfileError(
            f"{HOT} holds {before[HOT]}% of the samples, below the {FLOOR}% floor. ch27's census "
            "predicts it dominates; if it does not, the program or the prediction has changed."
        )

    symbols = sorted(set(before) | set(after))
    profile = {
        symbol: {
            "before_pct": before.get(symbol, 0.0),
            "after_pct": after.get(symbol, 0.0),
        }
        for symbol in symbols
        if before.get(symbol, 0.0) >= FLOOR or after.get(symbol, 0.0) >= FLOOR
    }

    if not annotated:
        raise ProfileError(
            f"perf annotate returned no per-instruction samples for {HOT}. Without them ch27's "
            "skid figure has nothing to show, and the chapter does not estimate one."
        )

    instructions = [
        {"offset": index, "text": text, "samples_pct": percent}
        for index, (percent, text) in enumerate(annotated)
    ]

    return [
        stamp_timing(
            "profile-host",
            {"symbols": profile, "floor_pct": FLOOR, "governor": governor()},
            ["bench/run_profilecost.py", PROGRAM, LIBRARY, HEADER],
            note="one arrangement per process, so each profile describes one of them",
            workload="sysfs/tools/tally.c scatter, then partitioned",
        ),
        stamp_timing(
            "skid-host",
            {"symbol": HOT, "instructions": instructions, "governor": governor()},
            ["bench/run_profilecost.py", PROGRAM, LIBRARY, HEADER],
            note="where the samples fell, uncorrected; the gap to the stalling instruction is "
            "the chapter's subject",
            workload="sysfs/tools/tally.c scatter, annotated",
        ),
    ]


#: The shapes this runner produces, one per result. See `bench/run_measuring.py` for why.
SHAPES = {
    "profile-host": {
        "symbols": {
            "sysfs_tally_scatter": {"before_pct": 88.8, "after_pct": 11.1},
            "sysfs_tally_partitioned": {"before_pct": 0.0, "after_pct": 77.7},
        },
        "floor_pct": 1.0,
        "governor": "performance",
    },
    "skid-host": {
        "symbol": "sysfs_tally_scatter",
        "instructions": [
            {"offset": 0, "text": "ldr w2, [x20, x4, lsl #2]", "samples_pct": 1.11},
            {"offset": 1, "text": "add w5, w5, #0x1", "samples_pct": 22.2},
        ],
        "governor": "performance",
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-run and compare; write nothing")
    args = parser.parse_args(argv)

    status = 0
    for payload in capture():
        if not args.check:
            path = write_result(payload)
            print(f"wrote {Path(path).relative_to(ROOT)}")
            continue
        try:
            committed = load_result(payload["name"])
        except FileNotFoundError:
            print(f"{payload['name']}: nothing committed to compare against")
            status = 1
            continue
        differences = measurement_differences(committed, payload)
        if not differences:
            print(f"{payload['name']}: unchanged")
            continue
        print(f"{payload['name']}: the measurement has moved")
        for difference in differences:
            print(f"  {difference}")
        status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
