#!/usr/bin/env python3
"""The two-routes chapter's price: what the routes cost, beside what their instruction counts predicted.

    python3 -m bench.run_bridgecost          # on the board only
    python3 -m bench.run_bridgecost --check  # re-run and compare; write nothing

`bench.run_bridge` already established what the two targets agree about: the same answer, the same
element count, and an instruction count for each route. This runner supplies the one thing that
agreement could not predict.

The predicted ratio is computed from those committed instruction counts rather than typed, so the
chapter's central comparison — a structural prediction against a measurement — cannot drift apart
from either side of itself.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/bridgecost.c"
HEADER = "sysfs/include/sysfs/bridge.h"
FIGURE = "the-same-program-on-both-targets-cost"


class BridgeCostError(RuntimeError):
    """The two routes stopped being comparable."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for line in text.splitlines():
        match line.split():
            case ["bridge", "cells", cells, "stride", stride]:
                facts |= {"cells": int(cells), "stride": int(stride)}
            case ["bridge", "agree", agree]:
                facts["agree"] = agree == "yes"
            case ["bridge", "sequential_ns", sequential, "chased_ns", chased]:
                facts |= {"sequential_ns": int(sequential), "chased_ns": int(chased)}
            case ["end", "bridgecost"]:
                facts["complete"] = True
    if not facts.get("complete"):
        raise BridgeCostError(f"bridgecost did not finish:\n{text[-2000:]}")
    return facts


def predicted_ratio() -> float:
    """What the instruction counts say the ratio should be, from the committed structural result.

    This is the number the two-routes chapter exists to falsify. It comes from `bridge-both`, which both targets
    agreed about, so the chapter's prediction and its measurement cannot drift apart.
    """
    counts = load_result("bridge-both")["summary"]["instructions"]["aarch64"]
    return counts["sysfs_bridge_chased"] / counts["sysfs_bridge_sequential"]


def capture() -> dict[str, Any]:
    require_board(FIGURE)
    facts = parse(timed_run([WORKLOAD], "bridgecost"))

    if not facts["agree"]:
        raise BridgeCostError(
            "the two routes computed different totals. The whole argument is that they agree "
            "about everything except cost; a disagreement makes this a comparison between two "
            "different programs."
        )
    if not facts["sequential_ns"]:
        raise BridgeCostError("the sequential route measured zero; the clock or the loop is gone")

    return stamp_timing(
        "bridge-host",
        {
            "bridge": {
                "cells": facts["cells"],
                "stride": facts["stride"],
                "sequential_ns": facts["sequential_ns"],
                "chased_ns": facts["chased_ns"],
                "predicted_ratio": predicted_ratio(),
            },
            "governor": governor(),
        },
        ["bench/run_bridgecost.py", WORKLOAD, HEADER],
        note="minimum of many runs; the predicted ratio comes from the committed bridge-both",
        workload="sysfs/bench/bridgecost.c",
    )


#: The shape this runner produces. See `bench/run_measuring.py` for why it is here.
SHAPE = {
    "bridge": {
        "cells": 111,
        "stride": 111,
        "sequential_ns": 111,
        "chased_ns": 222,
        "predicted_ratio": 1.11,
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
