#!/usr/bin/env python3
"""The optimisation chapter's price: what five spellings of one loop are worth once a compiler has had them.

    python3 -m bench.run_loopcost          # on the board only
    python3 -m bench.run_loopcost --check  # re-run and compare; write nothing

The driver reports the whole sweep rather than a per-element figure, and this runner divides. That
is deliberate: a sub-nanosecond cost floored by C's integer division is zero, which is what the
first version of this printed for all five variants — a table of zeroes that looked like a finding.

The five must agree about the answer. They are the same computation written five ways, and a
variant that has been hand-optimised into a different result is not an optimisation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/loopcost.c"
LIBRARY = "sysfs/lib/loops.c"
HEADER = "sysfs/include/sysfs/loops.h"
FIGURE = "optimising-code-cost"

#: How many digits of a per-element figure are worth printing. Two: the difference between the
#: variants is in the second one, and a third would be claiming a precision the clock's own
#: resolution does not support.
PLACES = 2


class LoopCostError(RuntimeError):
    """The five variants stopped being five spellings of one loop."""


def parse(text: str) -> dict[str, Any]:
    elements = 0
    loops: dict[str, dict[str, Any]] = {}
    complete = False
    for line in text.splitlines():
        match line.split():
            case ["loopcost", "elements", count]:
                elements = int(count)
            case ["loop", name, "total_ns", total, "agrees", agrees]:
                loops[name] = {"total_ns": int(total), "agrees": agrees == "yes"}
            case ["end", "loopcost"]:
                complete = True
    if not complete or not elements or not loops:
        raise LoopCostError(f"loopcost did not finish:\n{text[-2000:]}")
    return {"elements": elements, "loops": loops}


def capture() -> dict[str, Any]:
    require_board(FIGURE)
    facts = parse(timed_run([WORKLOAD, LIBRARY], "loopcost"))

    disagreed = sorted(name for name, data in facts["loops"].items() if not data["agrees"])
    if disagreed:
        raise LoopCostError(
            f"{disagreed} computed a different total from `plain`. The five are one computation "
            "written five ways, and the comparison is only a comparison while that holds."
        )
    empty = sorted(name for name, data in facts["loops"].items() if not data["total_ns"])
    if empty:
        raise LoopCostError(f"{empty} measured zero; the loop was removed rather than optimised")

    elements = facts["elements"]
    return stamp_timing(
        "loops-host",
        {
            "elements": elements,
            "loops": {
                name: round(data["total_ns"] / elements, PLACES)
                for name, data in facts["loops"].items()
            },
            "governor": governor(),
        },
        ["bench/run_loopcost.py", WORKLOAD, LIBRARY, HEADER],
        note="nanoseconds per element, divided here so a sub-nanosecond cost is not floored away",
        workload="sysfs/bench/loopcost.c",
    )


#: The shape this runner produces. See `bench/run_measuring.py` for why it is here.
SHAPE = {
    "elements": 111,
    "loops": {
        "plain": 1.11,
        "hoisted": 1.11,
        "reduced": 1.11,
        "unrolled": 2.22,
        "everything": 2.22,
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
