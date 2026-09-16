#!/usr/bin/env python3
"""Chapter 16's measurements: what the instrument costs, what one workload spreads over, and how
much of an answer is decided by something that cannot matter.

    python3 -m bench.run_measuring          # on the board only
    python3 -m bench.run_measuring --check  # re-run and compare; write nothing

Three invocations of `sysfs/bench/measuring.c`, which is the chapter's workload and prints one
fact per line. The runner does no statistics of its own: the distribution is summarised in C, by
`sysfs_summarise`, because that is the function ch21 argues about and a second implementation here
would be a second thing to trust.

The bias experiment is the one worth understanding before reading the numbers. The same work is
done three times, differing only in how many bytes of stack were claimed first — which changes
nothing about the computation and moves where its data lands in memory. Whether the timing follows
is the measurement rather than the assumption: this runner checks that the data really did move —
that the three runs landed the buffer at three different addresses — and records whatever the clock
then said, which on the reference board is the same number three times over.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/measuring.c"
FIGURE = "measuring-clock, measuring-spread and measuring-bias"

#: The paddings `measuring bias` uses, as the workload names them.
PADDINGS = ("0", "64", "512")


class MeasuringError(RuntimeError):
    """The workload did not produce the experiment the chapter describes."""


def summarise(parts: list[str]) -> dict[str, int]:
    """`<name> count N min N median N p90 N max N mean N` into a dict."""
    fields = parts[1:]
    return {fields[i]: int(fields[i + 1]) for i in range(0, len(fields), 2)}


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {"clock": {}, "bias": {}}
    complete = 0
    for line in text.splitlines():
        parts = line.split()
        match parts:
            case ["clock", field, value]:
                facts["clock"][field] = int(value)
            case ["spread", *_]:
                facts["spread"] = summarise(parts)
            case [name, *_] if name.startswith("bias_"):
                facts["bias"][name.removeprefix("bias_")] = summarise(parts)
            case ["end", "measuring"]:
                complete += 1
    if complete != 3:
        raise MeasuringError(f"expected three runs to finish, saw {complete}:\n{text[-2000:]}")
    return facts


def refuse_a_result_that_did_not_measure_anything(facts: dict[str, Any]) -> None:
    clock = facts["clock"]
    if not clock.get("cost_ns") or not clock.get("resolution_ns"):
        raise MeasuringError(
            "the clock reported a cost or a resolution of zero. Either the clock is not being "
            "read or the loop was optimised away; ch21 is about that number and cannot print a "
            "zero for it."
        )

    spread = facts["spread"]
    if spread["max"] <= spread["min"]:
        raise MeasuringError(
            "every repetition of the workload took exactly the same time. On a real machine that "
            "does not happen, and ch21's argument is that a single duration is an anecdote — a "
            "result with no spread in it would demonstrate the opposite."
        )

    missing = [p for p in PADDINGS if p not in facts["bias"]]
    if missing:
        raise MeasuringError(f"the bias experiment is missing paddings {missing}")
    # The check is on placement, not on effect. The chapter's honesty rests on the padding having
    # actually moved the data; if a compiler folded the claimed stack away, the three runs would be
    # one run and a flat timing would prove nothing. So the three must have landed the buffer at
    # three different addresses. Whether the *time* moved with it is then the measurement, and this
    # runner stamps it either way — on the reference board it does not move, which is the finding.
    bases = [facts["bias"][p].get("base") for p in PADDINGS]
    if any(base is None for base in bases):
        raise MeasuringError(
            "the bias experiment did not report where its data landed, so a run whose timing did "
            "not change cannot be told from a padding the compiler removed."
        )
    if len(set(bases)) != len(PADDINGS):
        raise MeasuringError(
            "two paddings placed the data at the same address, so the variable that should not "
            "matter moved nothing. The experiment has to move the data before a flat result can "
            "mean the machine is indifferent to where it is — check that the claimed stack was not "
            "optimised away."
        )


def capture() -> dict[str, Any]:
    require_board(FIGURE)
    printed = "".join(
        timed_run([WORKLOAD], "measuring", [what]) for what in ("clock", "spread", "bias")
    )
    facts = parse(printed)
    refuse_a_result_that_did_not_measure_anything(facts)

    return stamp_timing(
        "measuring-host",
        facts | {"governor": governor()},
        [
            "bench/run_measuring.py",
            WORKLOAD,
        ],
        note="three experiments, summarised in C by the same sysfs_summarise ch21 argues about",
        workload="sysfs/bench/measuring.c, run once per experiment",
    )


#: The shape this runner produces, with values that are obviously not measurements.
#:
#: It exists so `tests/test_board.py` can check today, with no board in the room, that what this
#: writes is what `bench/tables.py` reads. Getting that wrong is otherwise discovered on the one
#: day the hardware is available, which is the worst possible time.
#:
#: It is never written to `bench/results/`, and a test asserts that no committed result matches
#: it. The numbers are 111 and 222 so that one appearing in a rendered page would be unmistakable.
SHAPE = {
    "clock": {"cost_ns": 111, "resolution_ns": 222},
    "spread": {"count": 111, "min": 111, "median": 222, "p90": 222, "max": 222, "mean": 222},
    "bias": {
        "0": {"count": 111, "min": 111, "median": 222, "p90": 222, "max": 222, "mean": 222, "base": 100},
        "64": {"count": 111, "min": 111, "median": 222, "p90": 222, "max": 222, "mean": 222, "base": 200},
        "512": {"count": 111, "min": 111, "median": 222, "p90": 222, "max": 222, "mean": 222, "base": 300},
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
    # A timing that moved is not automatically wrong, unlike a listing that moved. It is reported
    # and the author decides, which is why this prints rather than explains.
    print(f"{payload['name']}: the measurement has moved\n")
    for difference in differences:
        print(f"  {difference}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
