#!/usr/bin/env python3
"""The pipeline chapter's measurements: what the core does between fetching an instruction and finishing it.

    python3 -m bench.run_pipelinecost          # on the board only, and needs perf counters
    python3 -m bench.run_pipelinecost --check  # re-run and compare; write nothing

Two sweeps, each one invocation of the workload per point so that `perf stat` counts that point
and nothing else.

    chain    the same arithmetic with one, two, four and eight independent accumulators. The
             dependence chain shortens; the instruction count does not. IPC is the figure.
    branch   the same arithmetic on the same multiset of values, reordered so that the branch
             is anywhere from perfectly predictable to not at all.

**The branch sweep uses `sysfs_count_over_calling` and not `sysfs_count_over`.** The chapter opens by
showing the compiler turning the plain one into a `cset` with no branch in it, and a branchless
loop cannot mispredict — measuring it would produce a flat line and a chapter concluding that
prediction does not matter. The first version of this runner did exactly that.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import (
    governor,
    perf_counters,
    require_board,
    require_perf,
    stamp_timing,
    timed_run,
)
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/pipelinecost.c"
LIBRARY = "sysfs/lib/pipeline.c"
HEADER = "sysfs/include/sysfs/pipeline.h"
FIGURE = "the-cpu-ilp and the-cpu-branches"

CHAINS = (1, 2, 4, 8)
PREDICTABILITY = (100, 90, 75, 50, 25, 0)
EVENTS = ["instructions", "cycles", "branches", "branch-misses"]


class PipelineCostError(RuntimeError):
    """The sweep stopped measuring what the chapter is about."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for line in text.splitlines():
        match line.split():
            case ["pipelinecost", "elements", count]:
                facts["elements"] = int(count)
            case ["chain", label, "total_ns", total, "answer", answer]:
                facts |= {"label": label, "total_ns": int(total), "answer": int(answer)}
            case ["branch", "predictable", pct, "total_ns", total, "answer", answer]:
                facts |= {
                    "predictable": int(pct),
                    "total_ns": int(total),
                    "answer": int(answer),
                }
    if "total_ns" not in facts:
        raise PipelineCostError(f"pipelinecost printed no timing:\n{text[-2000:]}")
    return facts


def _slope(xs: list[float], ys: list[float]) -> float:
    """Least squares through the points, which is the cost of one more of whatever x counts."""
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        raise PipelineCostError("every point has the same mispredict count; nothing to fit")
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denominator


def capture() -> dict[str, Any]:
    require_board(FIGURE)
    require_perf(FIGURE)

    variants: dict[str, Any] = {}
    answers = set()
    for width in CHAINS:
        printed = timed_run([WORKLOAD, LIBRARY], "pipelinecost", ["chain", str(width)])
        facts = parse(printed)
        counts = perf_counters(
            EVENTS, [str(ROOT / "sysfs" / "build" / "pipelinecost"), "chain", str(width)]
        )
        if "cycles" not in counts or "instructions" not in counts or not counts["cycles"]:
            raise PipelineCostError(
                "this PMU did not supply instructions and cycles, so IPC cannot be reported. "
                "the chapter's first table is IPC; it is not a figure this book will estimate."
            )
        answers.add(facts["answer"])
        variants[facts["label"]] = {
            "ns": round(facts["total_ns"] / facts["elements"], 2),
            "ipc": counts["instructions"] / counts["cycles"],
        }

    if len(answers) != 1:
        raise PipelineCostError(
            f"the chain widths computed different totals ({sorted(answers)}). They are one sum "
            "with a different number of accumulators, and the chapter compares them only while that holds."
        )

    points = []
    for predictable in PREDICTABILITY:
        printed = timed_run([WORKLOAD, LIBRARY], "pipelinecost", ["branch", str(predictable)])
        facts = parse(printed)
        counts = perf_counters(
            EVENTS, [str(ROOT / "sysfs" / "build" / "pipelinecost"), "branch", str(predictable)]
        )
        if "branch-misses" not in counts or "branches" not in counts:
            raise PipelineCostError(
                "this PMU has no branch or branch-miss counter, so the mispredict rate cannot be "
                "measured. The chapter says what it would take rather than estimating it."
            )
        points.append(
            {
                "predictable_percent": predictable,
                "mispredict_percent": 100 * counts["branch-misses"] / max(counts["branches"], 1),
                "misses": counts["branch-misses"],
                "ns": round(facts["total_ns"] / facts["elements"], 2),
                "answer": facts["answer"],
            }
        )

    if len({point["answer"] for point in points}) != 1:
        raise PipelineCostError(
            "the predictability levels counted different numbers of elements. The workload "
            "reorders one multiset precisely so the work is identical; different answers mean it "
            "is comparing two programs."
        )

    spread = max(p["mispredict_percent"] for p in points) - min(
        p["mispredict_percent"] for p in points
    )
    if spread < 1:
        raise PipelineCostError(
            f"the mispredict rate moved by {spread:.2f} points across the whole sweep. Either the "
            "compiler removed the branch — the chapter shows it doing exactly that to the other "
            "variant — or the counter is not counting."
        )

    # The slope of per-element time against the per-element mispredict *rate* — one branch per
    # element, so the fraction is mispredicts per element and the slope is nanoseconds per
    # mispredict. Regressing against the raw miss *count* instead mixes a per-element y with a
    # whole-run x and yields a number three-hundred-thousandths of the truth: the table read 0.0 ns.
    derived = _slope(
        [p["mispredict_percent"] / 100 for p in points],
        [float(p["ns"]) for p in points],
    )

    return stamp_timing(
        "pipeline-host",
        {
            "variants": variants,
            "branches": {"points": points, "derived_cost_ns": derived},
            "governor": governor(),
        },
        ["bench/run_pipelinecost.py", WORKLOAD, LIBRARY, HEADER],
        note="one process per point, so perf counts that point and nothing else",
        workload="sysfs/bench/pipelinecost.c",
    )


#: The shape this runner produces. See `bench/run_measuring.py` for why it is here.
SHAPE = {
    "variants": {
        "sysfs_sum_chain1": {"ns": 1.11, "ipc": 1.11},
        "sysfs_sum_chain8": {"ns": 2.22, "ipc": 2.22},
    },
    "branches": {
        "points": [
            {"predictable_percent": 100, "mispredict_percent": 1.11, "misses": 111, "ns": 1.11},
            {"predictable_percent": 0, "mispredict_percent": 22.2, "misses": 222, "ns": 2.22},
        ],
        "derived_cost_ns": 1.11,
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
