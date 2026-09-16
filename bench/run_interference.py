#!/usr/bin/env python3
"""The measurement chapter's interference experiment: what the radio does to the measured cores.

    python3 -m bench.run_interference          # on the board only; toggles the Wi-Fi radio
    python3 -m bench.run_interference --check   # re-run and compare; write nothing

ch01 recommends wiring the board rather than using its radio, on the mechanism that a wireless
driver takes interrupts and runs deferred work on the cores being measured. This measures the
claim rather than asserting it: the same fixed workload, run many times with the radio off and
again with it on, reported as what survived and what did not.

It is the one runner that deliberately makes the machine noisy, and the only one that has to
control the radio, so it is standalone rather than part of `make bench-board`, and it restores the
radio to off when it is done — the state every other measurement in this book is taken in.

The number to watch is the floor. Interference can only add time, never remove it, so the fastest
sample is the one it missed. If ch24's argument for the minimum is right, the radio will move the
mean and leave the floor exactly where it was.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from bench.board import NATIVE, governor, require_board, stamp_timing
from bench.measure import compile_program
from bench.stamp import ROOT, load_result, measurement_differences, write_result

WORKLOAD = "sysfs/bench/measuring.c"
FIGURE = "measuring-interference"

#: Spread runs per condition. Interference is intermittent, so one run proves nothing; this many
#: gives the disturbed fraction a denominator worth reading.
RUNS = 30

#: A run whose mean exceeds the floor by this much was disturbed by something other than the work.
DISTURBED = 1.1


class InterferenceError(RuntimeError):
    """The experiment could not be run, or the radio could not be controlled."""


def _radio(state: str) -> None:
    result = subprocess.run(
        ["sudo", "nmcli", "radio", "wifi", state], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise InterferenceError(
            f"could not turn the radio {state}: {result.stderr.strip()}\n"
            "This runner controls the Wi-Fi radio with `sudo nmcli`, so it runs on the board and "
            "needs sudo there. Everything else in Part V leaves the radio alone."
        )


def _radio_state() -> str:
    return subprocess.run(
        ["nmcli", "radio", "wifi"], capture_output=True, text=True, check=False
    ).stdout.strip()


def _associated() -> bool:
    """True once the driver has a link up — which is when it starts doing work on the cores."""
    try:
        return Path("/sys/class/net/wlan0/operstate").read_text().strip() == "up"
    except OSError:
        return False


def _spread_once(built: Any) -> dict[str, int]:
    printed = built.run(["spread"]).stdout
    for line in printed.splitlines():
        parts = line.split()
        if parts and parts[0] == "spread":
            return {parts[i]: int(parts[i + 1]) for i in range(1, len(parts) - 1, 2)}
    raise InterferenceError(f"measuring spread printed no distribution:\n{printed}")


def _condition(built: Any, radio: str) -> dict[str, Any]:
    """Run the workload `RUNS` times and reduce it to the floor and the damage above it."""
    mins, means, maxes = [], [], []
    for _ in range(RUNS):
        summary = _spread_once(built)
        mins.append(summary["min"])
        means.append(summary["mean"])
        maxes.append(summary["max"])
    floor = min(mins)
    return {
        "radio": radio,
        "floor_ns": floor,
        "best_mean_ns": min(means),
        "worst_mean_ns": max(means),
        "worst_max_ns": max(maxes),
        "disturbed_runs": sum(1 for mean in means if mean > floor * DISTURBED),
    }


def capture() -> dict[str, Any]:
    require_board(FIGURE)
    built = compile_program(
        [WORKLOAD, "sysfs/lib/timing.c"],
        ROOT / "sysfs" / "build" / "interference",
        NATIVE,
        includes=["sysfs/include"],
    )

    original = _radio_state()
    try:
        _radio("off")
        time.sleep(2)
        quiet = _condition(built, "off")

        _radio("on")
        for _ in range(20):  # let the driver associate; that is when it starts taking interrupts
            if _associated():
                break
            time.sleep(1)
        radio = _condition(built, "on, associated" if _associated() else "on, not associated")
    finally:
        _radio("off")  # leave the board the way every other measurement here needs it

    return stamp_timing(
        "interference-host",
        {
            "runs_per_condition": RUNS,
            "disturbed_threshold": DISTURBED,
            "quiet": quiet,
            "radio": radio,
            "governor": governor(),
            "original_radio": original,
        },
        ["bench/run_interference.py", WORKLOAD],
        note="the same spread workload with the radio off and then on; restored to off after",
        workload="sysfs/bench/measuring.c spread, run many times per condition",
    )


#: The shape this runner writes, for `tests/test_board.py`. Values are obviously not measurements.
SHAPE = {
    "runs_per_condition": 111,
    "disturbed_threshold": 1.1,
    "quiet": {
        "radio": "off",
        "floor_ns": 111,
        "best_mean_ns": 111,
        "worst_mean_ns": 111,
        "worst_max_ns": 222,
        "disturbed_runs": 0,
    },
    "radio": {
        "radio": "on, associated",
        "floor_ns": 111,
        "best_mean_ns": 111,
        "worst_mean_ns": 222,
        "worst_max_ns": 222,
        "disturbed_runs": 222,
    },
    "governor": "performance",
    "original_radio": "disabled",
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
    # Interference is stochastic, so a moved number here is expected rather than alarming; the
    # floor is the part that should hold. This prints and lets the author judge.
    print(f"{payload['name']}: the measurement has moved (interference is stochastic)\n")
    for difference in differences:
        print(f"  {difference}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
