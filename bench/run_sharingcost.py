#!/usr/bin/env python3
"""Chapter 20's measurements: what four cores cost each other.

    python3 -m bench.run_sharingcost          # on the board only
    python3 -m bench.run_sharingcost --check  # re-run and compare; write nothing

Two experiments. The first has no shared data in it at all — each thread increments its own
counter, and the only difference between the arrangements is whether those counters land on one
cache line. The second contends on purpose: the same atomic operation on a counter every thread
writes, against one each has to itself.

**This runner refuses a flat first experiment**, and that refusal is the reason it is worth
reading. The packed layout must be meaningfully slower than the padded one; if it is not, either
the counters are not where the layout says they are or the threads are not running at the same
time, and in both cases ch25's headline figure would be a table showing that false sharing costs
nothing.

Neither the magnitude nor the direction can be checked anywhere but the board, so nothing here is
tuned against a development machine. What is checked off the board is that the workload reports
the counters sharing a line when it says packed and not sharing one when it says padded.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/sharingcost.c"
LIBRARIES = ["sysfs/lib/sharing.c", "sysfs/lib/ordering.c"]
HEADERS = ["sysfs/include/sysfs/sharing.h", "sysfs/include/sysfs/ordering.h"]
FIGURE = "memory-ordering-on-real-hardware-sharing and memory-ordering-on-real-hardware-atomics"

THREADS = (2, 4)
LAYOUTS = ("packed", "padded")
OPERATIONS = ("plain", "relaxed", "ordered")

#: How much slower the packed layout has to be before this counts as having measured false
#: sharing rather than noise. Deliberately modest: a bar set at the expected size would be
#: assuming the answer, and the reference board's four Cortex-A76 cores settle at about 1.48x —
#: a stable, real effect, but half again rather than several times over. The floor sits below
#: that with headroom for a different kernel or firmware, and only has to catch a flat result.
CONTENDED = 1.3


class SharingCostError(RuntimeError):
    """The experiment stopped demonstrating what ch25 says it demonstrates."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for line in text.splitlines():
        match line.split():
            case ["sharing", "threads", threads, "layout", layout, "total_ns", total,
                  "increments", increments, "same_line", same]:  # fmt: skip
                facts = {
                    "threads": int(threads),
                    "layout": layout,
                    "total_ns": int(total),
                    "increments": int(increments),
                    "same_line": same == "1",
                }
            case ["atomics", "op", op, "threads", threads, "where", where, "total_ns", total,
                  "increments", increments]:  # fmt: skip
                facts = {
                    "op": op,
                    "threads": int(threads),
                    "where": where,
                    "total_ns": int(total),
                    "increments": int(increments),
                }
    if not facts:
        raise SharingCostError(f"sharingcost printed no measurement:\n{text[-2000:]}")
    return facts


def _run(args: list[str]) -> dict[str, Any]:
    return parse(timed_run([WORKLOAD, *LIBRARIES], "sharingcost", args))


def capture() -> dict[str, Any]:
    require_board(FIGURE)

    points = []
    for threads in THREADS:
        for layout in LAYOUTS:
            facts = _run(["sharing", str(threads), layout])
            expected_sharing = layout == "packed"
            if facts["same_line"] != expected_sharing:
                raise SharingCostError(
                    f"the {layout} layout reported same_line={facts['same_line']}, and ch25 is "
                    f"about it being {expected_sharing}. The arena is line-aligned precisely so "
                    "this holds; if it has stopped, the two arrangements are one arrangement."
                )
            points.append(
                {
                    "threads": threads,
                    "layout": layout,
                    "ns": round(facts["total_ns"] / facts["increments"], 2),
                }
            )

    for threads in THREADS:
        packed = next(
            p["ns"] for p in points if p["threads"] == threads and p["layout"] == "packed"
        )
        padded = next(
            p["ns"] for p in points if p["threads"] == threads and p["layout"] == "padded"
        )
        if packed < padded * CONTENDED:
            raise SharingCostError(
                f"at {threads} threads the packed layout cost {packed} ns and the padded one "
                f"{padded} ns, which is not the {CONTENDED}x this needs to be a measurement of "
                "false sharing rather than of noise. Either the counters are not where the "
                "layout says, or the threads are not running at the same time — check that this "
                "machine has the cores it thinks it has before changing the threshold."
            )

    atomics: dict[str, Any] = {}
    for op in OPERATIONS:
        contended = _run(["atomics", op, str(max(THREADS)), "shared"])
        uncontended = _run(["atomics", op, str(max(THREADS)), "own"])
        atomics[op] = {
            "uncontended_ns": round(uncontended["total_ns"] / uncontended["increments"], 2),
            "contended_ns": round(contended["total_ns"] / contended["increments"], 2),
            "threads": max(THREADS),
        }

    return stamp_timing(
        "sharing-host",
        {
            "sharing": {"points": points},
            "atomics": atomics,
            "governor": governor(),
        },
        ["bench/run_sharingcost.py", WORKLOAD, *LIBRARIES, *HEADERS],
        note="nanoseconds per increment, across all threads; the first experiment shares no data",
        workload="sysfs/bench/sharingcost.c",
    )


#: The shape this runner produces. See `bench/run_measuring.py` for why it is here.
SHAPE = {
    "sharing": {
        "points": [
            {"threads": 2, "layout": "packed", "ns": 22.2},
            {"threads": 2, "layout": "padded", "ns": 1.11},
        ]
    },
    "atomics": {
        "plain": {"uncontended_ns": 1.11, "contended_ns": 22.2, "threads": 4},
        "ordered": {"uncontended_ns": 1.11, "contended_ns": 22.2, "threads": 4},
    },
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
