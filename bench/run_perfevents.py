#!/usr/bin/env python3
"""Appendix C's inventory: the perf events this board exposes, and which it counts.

    python3 -m bench.run_perfevents          # on the board only
    python3 -m bench.run_perfevents --check   # re-run and compare; write nothing

Everything Appendix C states about *this machine* comes from here; everything it states about what
an event *means* cites a primary source. Which events exist, which are hardware and which the kernel
keeps in software, and how many the PMU can count at once before perf begins time-sharing counters
and scaling the answer — all of it is a property of the silicon, the kernel and the firmware
together, so it is asked of the machine rather than looked up.

The counter count is found by asking, not by reading a register: perf is given one more event at a
time over a fixed workload until one of them stops running for the whole of it. The largest set that
all ran at 100% is how many the hardware has; the first set that did not is the one perf had to
estimate.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from bench.stamp import (
    ROOT,
    build_result,
    classify_machine,
    describe_board,
    load_result,
    measurement_differences,
    write_result,
)

PMU_ROOT = Path("/sys/bus/event_source/devices")

#: A workload on-CPU long enough for perf to rotate counters fairly. Too short and even seven events
#: report less than 100% simply because the run ended mid-rotation, which would fake multiplexing.
_SPIN = "x = 0\nfor _ in range(120_000_000):\n    x += 1\n"

#: The most events to try before giving up looking for the ceiling.
_MAX_PROBE = 12


def _perf(*args: str) -> str:
    return subprocess.run(["perf", *args], capture_output=True, text=True, check=False).stdout


def _cpu_pmu() -> str:
    """The CPU PMU: the event-source device that publishes a directory of raw events."""
    for device in sorted(PMU_ROOT.iterdir()):
        events = device / "events"
        if events.is_dir() and any(events.iterdir()):
            return device.name
    raise SystemExit("no CPU PMU with a raw-event directory was found under " + str(PMU_ROOT))


def _raw_events(pmu: str) -> list[str]:
    return sorted(path.name for path in (PMU_ROOT / pmu / "events").iterdir())


def _generic(category: str) -> list[str]:
    """The event names `perf list <category>` offers, without the `foo OR bar` aliases."""
    names = []
    for line in _perf("list", category).splitlines():
        match = re.match(r"^\s{2}([A-Za-z][\w\-]+)\b", line)
        if match and not line.strip().endswith(":"):
            names.append(match.group(1))
    return sorted(set(names))


def _enabled_percentages(events: list[str]) -> list[float]:
    """Run `perf stat` with these events over the fixed spin; return each one's % enabled."""
    probe = subprocess.run(
        ["perf", "stat", "-x,", "-e", ",".join(events), "--", sys.executable, "-c", _SPIN],
        capture_output=True,
        text=True,
        check=False,
    )
    percentages = []
    for line in (probe.stderr + probe.stdout).splitlines():
        fields = line.split(",")
        if len(fields) >= 5 and fields[0].strip() not in ("", "<not counted>", "<not supported>"):
            try:
                percentages.append(float(fields[4]))
            except ValueError:
                continue
    return percentages


def _count_counters(generic_hardware: list[str]) -> dict[str, Any]:
    """How many events run at once before perf multiplexes, found by asking the machine."""
    ceiling = 0
    scaled_to = 100.0
    for count in range(1, min(len(generic_hardware), _MAX_PROBE) + 1):
        percentages = _enabled_percentages(generic_hardware[:count])
        if percentages and min(percentages) >= 99.5:
            ceiling = count
        else:
            scaled_to = round(min(percentages), 1) if percentages else 0.0
            break
    return {
        "counters": ceiling,
        "oversubscribed_at": ceiling + 1,
        "scaled_enabled_pct": scaled_to,
    }


def capture() -> dict[str, Any]:
    kind = classify_machine()
    if kind != "board":
        raise SystemExit(
            f"Appendix C is a property of one machine, and this is a {kind!r} one.\n"
            "Run it over SSH on the board:  python3 -m bench.run_perfevents"
        )
    if not (bin_perf := subprocess.run(["which", "perf"], capture_output=True, text=True).stdout):
        raise SystemExit("perf is not installed; see the board chapter")

    pmu = _cpu_pmu()
    generic_hardware = _generic("hw")
    summary = {
        "pmu": pmu,
        "raw_events": _raw_events(pmu),
        "generic_hardware": generic_hardware,
        "generic_cache": _generic("cache"),
        "software_events": _generic("sw"),
        **_count_counters(generic_hardware),
    }
    summary["raw_event_count"] = len(summary["raw_events"])

    version = _perf("--version").strip() or "perf (version unknown)"
    return build_result(
        name="perfevents-host",
        target="host",
        summary=summary,
        code_sources=["bench/run_perfevents.py"],
        toolchain={
            "tool": version,
            "path": bin_perf.strip(),
            "execution": "native on the board — an inventory, not a timing",
        },
        machine=describe_board(),
        conditions={
            "note": "which events this silicon, kernel and firmware expose, and how many count at once"
        },
    )


#: The shape this writes, for `tests/test_board.py`.
SHAPE = {
    "pmu": "armv8_cortex_aXX",
    "raw_events": ["one_raw_event", "another_raw_event"],
    "raw_event_count": 111,
    "generic_hardware": ["cpu-cycles", "instructions"],
    "generic_cache": ["L1-dcache-loads"],
    "software_events": ["cpu-clock", "page-faults"],
    "counters": 111,
    "oversubscribed_at": 222,
    "scaled_enabled_pct": 22.2,
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
    print(
        f"{payload['name']}: the inventory has changed (a kernel or firmware update can do this)\n"
    )
    for difference in differences:
        print(f"  {difference}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
