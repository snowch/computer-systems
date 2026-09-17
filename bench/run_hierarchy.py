#!/usr/bin/env python3
"""The memory-hierarchy chapter's measurements: where the data is, found by asking rather than by looking it up.

    python3 -m bench.run_hierarchy          # on the board only
    python3 -m bench.run_hierarchy --check  # re-run and compare; write nothing

Three sweeps of `sysfs/bench/hierarchy.c`, each a dependent-load chase so that the machine cannot
overlap one access with the next and what comes back is a latency rather than a throughput.

    sizes    the same access pattern over a growing working set. The steps are the levels.
    stride   a fixed number of visits with a growing gap. The step is the cache line.
    reach    one visit per page. The step is how far the TLB reaches.

**The derived figures are derived, not read.** `_steps` finds where the curve jumps and turns that
into a line size and a level boundary; the vendor's own numbers are read separately out of sysfs
and recorded beside them. Where they disagree the chapter prints both and says the measurement
wins — a specification is a claim about a product line and this is a statement about the silicon
that produced the number.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/hierarchy.c"
FIGURE = (
    "the-memory-hierarchy-levels, the-memory-hierarchy-line, the-memory-hierarchy-reach and "
    "the-memory-hierarchy-vendor"
)

#: How much slower one point has to be than the one before it to count as a step rather than as
#: noise. A latency curve over a cache boundary roughly doubles; a run-to-run wobble does not
#: come close. Stated as a constant because it is a judgement, and a judgement in a runner should
#: be visible rather than buried in an expression.
STEP = 1.4

#: The page size the reach sweep walks, one visit per page. Sv39 and AArch64's 4 KiB granule
#: agree on it, and `sysfs/bench/hierarchy.c` steps by exactly this much.
PAGE_BYTES = 4096

CACHE_SYSFS = Path("/sys/devices/system/cpu/cpu0/cache")


class HierarchyError(RuntimeError):
    """The sweep did not produce a curve with a hierarchy in it."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {"sizes": [], "stride": [], "reach": [], "clock": {}}
    complete = 0
    for line in text.splitlines():
        parts = line.split()
        match parts:
            case ["clock", field, value]:
                facts["clock"][field] = int(value)
            case ["size", "bytes", byte_count, "ns", ns]:
                facts["sizes"].append({"bytes": int(byte_count), "ns": int(ns)})
            case ["stride", "bytes", byte_count, "ns", ns]:
                facts["stride"].append({"bytes": int(byte_count), "ns": int(ns)})
            case ["reach", "pages", pages, "ns", ns]:
                facts["reach"].append({"pages": int(pages), "ns": int(ns)})
            case ["end", "hierarchy"]:
                complete += 1
    if complete != 3:
        raise HierarchyError(f"expected three sweeps to finish, saw {complete}:\n{text[-2000:]}")
    return facts


def _steps(points: list[dict[str, int]], axis: str) -> list[int]:
    """The x-values at which the curve jumped by more than :data:`STEP`."""
    found = []
    for before, after in zip(points, points[1:], strict=False):
        if before["ns"] and after["ns"] / before["ns"] >= STEP:
            found.append(after[axis])
    return found


def vendor_caches() -> dict[str, int]:
    """What the running kernel says this core's caches are, in bytes.

    Read from sysfs rather than from a datasheet, and recorded so the chapter can show the two
    side by side. Absent on a machine that does not publish it, which is not an error — the
    measurement is the figure and this is the comparison.
    """
    found: dict[str, int] = {}
    if not CACHE_SYSFS.is_dir():
        return found
    for index in sorted(CACHE_SYSFS.glob("index*")):
        try:
            level = int((index / "level").read_text().strip())
            kind = (index / "type").read_text().strip()
            size = (index / "size").read_text().strip()
            line = int((index / "coherency_line_size").read_text().strip())
        except (OSError, ValueError):
            continue
        found.setdefault("line_bytes", line)
        if kind == "Instruction":
            continue
        scale = {"K": 1024, "M": 1024 * 1024}.get(size[-1].upper(), 1)
        found[f"l{level}_bytes"] = int(size.rstrip("KMkm")) * scale
    return found


def derive(facts: dict[str, Any]) -> dict[str, Any]:
    line_steps = _steps(facts["stride"], "bytes")
    size_steps = _steps(facts["sizes"], "bytes")
    if not line_steps:
        raise HierarchyError(
            "the stride sweep is flat: no gap between visits made the chase slower. Either the "
            "chain is not being followed or the compiler removed it, and the line-size figure "
            "cannot come from a curve with no step in it."
        )
    if not size_steps:
        raise HierarchyError(
            "the size sweep is flat: growing the working set cost nothing. That would mean there "
            "is no hierarchy to measure, which is the one thing the chapter is about."
        )

    vendor = vendor_caches()
    derived: dict[str, Any] = {
        # The step is where consecutive visits stopped sharing a line, so the line is the stride
        # *before* it.
        "line_bytes": line_steps[0] // 2,
        "line_bytes_vendor": vendor.get("line_bytes", "not published"),
    }
    # Each step in the size sweep is a level boundary: the last size that still fitted.
    for level, step in zip((1, 2, 3), size_steps, strict=False):
        derived[f"l{level}_bytes"] = step // 2
    for level in (1, 2, 3):
        derived.setdefault(f"l{level}_bytes", "no step found")
        derived[f"l{level}_bytes_vendor"] = vendor.get(f"l{level}_bytes", "not published")

    # The reach sweep was collected from the start and derived from by nothing, so the chapter's
    # section on translation had no figure of its own and included the vendor comparison instead.
    # The step is the last page count that still fitted, which is what a TLB reaches.
    reach_steps = _steps(facts["reach"], "pages")
    derived["tlb_reach_pages"] = reach_steps[0] // 2 if reach_steps else "no step found"
    derived["tlb_reach_bytes"] = (
        derived["tlb_reach_pages"] * PAGE_BYTES
        if isinstance(derived["tlb_reach_pages"], int)
        else "no step found"
    )
    return derived


def capture() -> dict[str, Any]:
    require_board(FIGURE)
    printed = "".join(
        timed_run([WORKLOAD], "hierarchy", [what]) for what in ("sizes", "stride", "reach")
    )
    facts = parse(printed)
    facts["derived"] = derive(facts)

    return stamp_timing(
        "hierarchy-host",
        facts | {"governor": governor()},
        ["bench/run_hierarchy.py", WORKLOAD],
        note="dependent-load chases, so each figure is a latency rather than a throughput",
        workload="sysfs/bench/hierarchy.c, run once per sweep",
    )


#: The shape this runner produces. See `bench/run_measuring.py` for why it is here.
SHAPE = {
    "clock": {"cost_ns": 111},
    "sizes": [{"bytes": 1024, "ns": 111}, {"bytes": 2048, "ns": 222}],
    "stride": [{"bytes": 8, "ns": 111}, {"bytes": 64, "ns": 222}],
    "reach": [{"pages": 4, "ns": 111}],
    "derived": {
        "line_bytes": 111,
        "line_bytes_vendor": 222,
        "l1_bytes": 111,
        "l1_bytes_vendor": 222,
        "l2_bytes": 111,
        "l2_bytes_vendor": 222,
        "l3_bytes": 111,
        "l3_bytes_vendor": 222,
        "tlb_reach_pages": 111,
        "tlb_reach_bytes": 222,
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
