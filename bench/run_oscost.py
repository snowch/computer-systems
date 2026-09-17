#!/usr/bin/env python3
"""The OS-cost chapter's measurements: what Linux charges for the three services Part IV took apart.

    python3 -m bench.run_oscost          # on the board only
    python3 -m bench.run_oscost --check  # re-run and compare; write nothing

Writes three results from one workload, because they are three questions about one boundary:
what the services cost beside their baselines, what separates a minor fault from a major one, and
what the vDSO saves.

Two refusals, both about the same failure — a table that looks right and measures nothing.

The workload reports whether its raw system call is really the trapping instruction or fell
through to libc, which it does on any architecture but this book's two. A build that fell through
compares the vDSO route with itself and prints two identical numbers, which is what an x86
development machine printed while this was being written.

And the two clock routes must actually differ. If they do not on the board, either the vDSO is not
being used or the raw path is not trapping, and `the-os-layers-cost-vdso`'s entire point is the gap between them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/oscost.c"
FIGURE = "the-os-layers-cost-cost, the-os-layers-cost-faults and the-os-layers-cost-vdso"

#: What each service is measured against. Chosen to be unflattering: in each pair the difference
#: is doing the thing against not doing it.
BASELINES = {
    "syscall": "an empty function call",
    "fault": "a touch of a page already mapped",
    "switch": "the same round trip without leaving the thread",
}

SATISFIED_FROM = {
    "none": "nothing — it is mapped and resident",
    "minor": "a zeroed page the kernel already had",
    "major": "storage",
}

#: How far apart the two clock routes have to be before this is a measurement of the vDSO rather
#: than of one route twice.
DISTINCT = 1.5


class OsCostError(RuntimeError):
    """The workload stopped measuring the boundary."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {"services": {}, "faults": {}, "routes": {}}
    for line in text.splitlines():
        match line.split():
            case ["oscost", "rounds", _, "pages", _, "raw_route", route]:
                facts["raw_route"] = route
            case ["service", name, "total_ns", total, "baseline_total_ns", base, "over", over]:
                facts["services"][name] = {
                    "total_ns": int(total),
                    "baseline_total_ns": int(base),
                    "over": int(over),
                }
            case ["fault", kind, "ns", ns]:
                facts["faults"][kind] = int(ns)
            case ["route", call, route, "total_ns", total, "over", over]:
                facts["routes"][f"{call} ({route})"] = {
                    "route": route,
                    "total_ns": int(total),
                    "over": int(over),
                }
    return facts


def _per(entry: dict[str, int], key: str = "total_ns") -> float:
    return round(entry[key] / entry["over"], 2)


def capture() -> list[dict[str, Any]]:
    require_board(FIGURE)

    services = parse(timed_run([WORKLOAD], "oscost", ["services"], extra_flags=["-lpthread"]))
    faults = parse(timed_run([WORKLOAD], "oscost", ["faults"], extra_flags=["-lpthread"]))
    routes = parse(timed_run([WORKLOAD], "oscost", ["vdso"], extra_flags=["-lpthread"]))

    if services.get("raw_route") != "raw":
        raise OsCostError(
            "the workload's raw system call fell through to libc, which it does on any "
            "architecture but this book's two. Every figure below would then be comparing a "
            "route with itself."
        )

    priced = {}
    for name, entry in services["services"].items():
        each = _per(entry)
        baseline = _per(entry, "baseline_total_ns")
        if not each:
            raise OsCostError(f"{name} measured zero")
        priced[name] = {
            "ns": each,
            "baseline": BASELINES[name],
            "baseline_ns": baseline,
            "ratio": round(each / baseline, 1) if baseline else "no baseline to divide by",
        }

    if faults["faults"].get("major", 0) <= faults["faults"].get("minor", 0):
        raise OsCostError(
            f"a major fault measured {faults['faults'].get('major')} ns and a minor one "
            f"{faults['faults'].get('minor')} ns. The chapter's claim is that waiting for storage is "
            "orders of magnitude worse; if it is not, posix_fadvise did not drop the page cache "
            "and the 'major' fault was served from memory."
        )

    clock_routes = {k: v for k, v in routes["routes"].items() if "clock_gettime" in k}
    if len(clock_routes) == 2:
        fast, slow = sorted(_per(v) for v in clock_routes.values())
        if fast and slow < fast * DISTINCT:
            raise OsCostError(
                f"the two clock routes measured {fast} ns and {slow} ns, which is not the "
                f"{DISTINCT}x this needs to be a measurement of the vDSO. Either the library call "
                "is not using it or the raw path is not trapping."
            )

    return [
        stamp_timing(
            "oscost-host",
            {"services": priced, "governor": governor()},
            ["bench/run_oscost.py", WORKLOAD],
            note="each service beside an unflattering baseline; the ratio is what survives a "
            "change of machine",
            workload="sysfs/bench/oscost.c services",
        ),
        stamp_timing(
            "faultcost-host",
            {
                "faults": {
                    kind: {"ns": ns, "satisfied_from": SATISFIED_FROM[kind]}
                    for kind, ns in faults["faults"].items()
                },
                "governor": governor(),
            },
            ["bench/run_oscost.py", WORKLOAD],
            note="the major fault's page cache is dropped with posix_fadvise, which needs no "
            "privilege",
            workload="sysfs/bench/oscost.c faults",
        ),
        stamp_timing(
            "vdso-host",
            {
                "routes": {
                    call: {"route": entry["route"], "ns": _per(entry)}
                    for call, entry in routes["routes"].items()
                },
                "governor": governor(),
            },
            ["bench/run_oscost.py", WORKLOAD],
            note="the same request by two routes, one of which changes privilege level",
            workload="sysfs/bench/oscost.c vdso",
        ),
    ]


#: The shapes this runner produces, one per result. See `bench/run_measuring.py` for why.
SHAPES = {
    "oscost-host": {
        "services": {
            "syscall": {
                "ns": 111.0,
                "baseline": "an empty function call",
                "baseline_ns": 1.11,
                "ratio": 111.0,
            },
        },
        "governor": "performance",
    },
    "faultcost-host": {
        "faults": {
            "minor": {"ns": 111, "satisfied_from": "a zeroed page the kernel already had"},
            "major": {"ns": 222, "satisfied_from": "storage"},
        },
        "governor": "performance",
    },
    "vdso-host": {
        "routes": {
            "clock_gettime (vdso)": {"route": "vdso", "ns": 1.11},
            "clock_gettime (trap)": {"route": "trap", "ns": 222.0},
        },
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
