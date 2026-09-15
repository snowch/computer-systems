"""The plumbing every board measurement shares, so that twelve runners are not twelve policies.

    from bench.board import require_board, timed_run, stamp_timing

Each `host` result in Part IV answers a different question, but the way it is obtained is the same
every time: refuse to run anywhere but the machine being measured, build the workload with the
board's own compiler, run it for its numbers, and stamp the result with a machine block read off
the running system rather than a datasheet.

**The refusal is the point of this module.** It is the one rule the book's credibility rests on:
an emulated duration is indistinguishable from a real one once it is a number in a table. Every
runner here calls :func:`require_board` before it does anything else, and `bench.stamp` refuses
the result a second time on the way out, so a `host` timing taken on a laptop fails twice.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from bench.measure import COMMON_FLAGS, HostTarget, compile_program
from bench.stamp import ROOT, build_result, classify_machine, compiler_version, describe_board

#: The board builds with its own compiler, natively. No cross toolchain, no emulation, and the
#: flags every host measurement is taken at.
NATIVE = HostTarget(
    name="board-native",
    cc="cc",
    flags=COMMON_FLAGS,
    trustworthy_for_timing=True,
    why="the machine being measured, compiling for itself",
)

#: What every `host` result names as core, on top of `bench.stamp.TARGET_SOURCES`.
TIMING_SOURCES = ("sysfs/lib/timing.c", "sysfs/include/sysfs/timing.h")


class NotTheBoardError(SystemExit):
    """Raised, and not caught, when a host measurement is attempted anywhere else."""


def require_board(what: str) -> None:
    """Decline to measure unless this is the machine the book measures.

    `what` names the figure, so the message says which measurement was refused rather than
    leaving the reader to work it out from a traceback.
    """
    kind = classify_machine()
    if kind != "board":
        raise NotTheBoardError(
            f"{what} is a `host` measurement and this is a {kind!r} machine.\n"
            "Run it on the machine being measured:  make bench-board\n"
            "An emulated duration is not a slow measurement, it is not a measurement; see ch00."
        )


def timed_run(
    sources: list[str],
    name: str,
    args: list[str] | None = None,
    *,
    includes: list[str] | None = None,
) -> str:
    """Build a workload against the book's clock and run it, returning what it printed.

    Every workload links `sysfs/lib/timing.c`, because every duration in Part IV is read through
    the one clock ch16 built and argued about. A runner that timed with its own `clock_gettime`
    would be a second, unexamined instrument.
    """
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    built = compile_program(
        [*sources, "sysfs/lib/timing.c"],
        build_dir / name,
        NATIVE,
        includes=includes or ["sysfs/include"],
    )
    return built.run(args or []).stdout


def stamp_timing(
    name: str,
    summary: dict[str, Any],
    code_sources: list[str],
    *,
    note: str,
    workload: str,
) -> dict[str, Any]:
    """Stamp a board timing, with the provenance a duration has to carry.

    ``kind`` is left as the default measurement: these are the results the whole stamping scheme
    exists for, and they are held to the strictest rules rather than the compiled-kind exemption.
    """
    return build_result(
        name=name,
        target="host",
        summary=summary,
        code_sources=[*code_sources, *TIMING_SOURCES],
        toolchain={
            "cc": compiler_version(NATIVE.cc),
            "flags": " ".join(NATIVE.flags),
            "execution": "native on the machine being measured",
        },
        machine=describe_board(),
        conditions={"note": note, "workload": workload},
    )


def governor() -> str:
    """Which CPU frequency governor is in force, recorded because it changes every number here.

    Not enforced. A reader measuring on a board set to `ondemand` gets different figures from one
    set to `performance`, and the useful thing is that the result says which rather than that the
    runner refuses to proceed.
    """
    path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    try:
        return path.read_text().strip()
    except OSError:
        return "unknown"


def perf_available() -> bool:
    """Whether `perf` can be run at all here.

    Catches OSError rather than letting it out. A missing binary raises FileNotFoundError from
    subprocess, so the obvious one-liner turns "perf is not installed" — the single most likely
    state of a board out of its box — into a traceback rather than the message below that says
    how to fix it. Found by running it on a machine without perf.
    """
    try:
        return (
            subprocess.run(["perf", "--version"], capture_output=True, check=False).returncode == 0
        )
    except OSError:
        return False


class PerfUnavailableError(RuntimeError):
    """perf is missing, or this kernel will not let this user read counters."""


#: What the kernel has to allow before an unprivileged process may count anything.
PARANOID = Path("/proc/sys/kernel/perf_event_paranoid")


def require_perf(what: str) -> None:
    """Fail with the remedy rather than with a traceback.

    Both failures are ordinary on a fresh machine and both have a one-line fix, so saying which
    happened is worth more than any amount of stack. `scripts/verify-setup.py` checks the same two
    things, so a reader who ran it has seen this once already.
    """
    if not perf_available():
        raise PerfUnavailableError(
            f"{what} needs perf, which is not on PATH.\n"
            "  Debian / Ubuntu / Raspberry Pi OS:  sudo apt install linux-perf"
        )
    try:
        paranoid = PARANOID.read_text().strip()
    except OSError:
        paranoid = "unreadable"
    probe = subprocess.run(
        ["perf", "stat", "-e", "instructions", "true"], capture_output=True, text=True, check=False
    )
    if probe.returncode != 0:
        last = probe.stderr.strip().splitlines()
        raise PerfUnavailableError(
            f"{what} needs perf counters and this kernel refused them "
            f"(perf_event_paranoid={paranoid}).\n"
            "  sudo sysctl kernel.perf_event_paranoid=1\n"
            f"perf said: {last[-1] if last else 'nothing'}"
        )


def perf_counters(events: list[str], command: list[str]) -> dict[str, int]:
    """Count `events` over one run of `command`, as event name to count.

    `-x,` asks for machine-readable output rather than perf's aligned report, because parsing the
    report means parsing thousands separators that depend on the locale.

    A counter this hardware does not have comes back as `<not supported>` and is recorded as
    absent rather than as zero. Zero is a measurement; not having the counter is not, and a
    chapter that printed 0% mispredicts because the PMU lacks the event would be worse than one
    that printed nothing.
    """
    result = subprocess.run(
        ["perf", "stat", "-x,", "-e", ",".join(events), "--", *command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PerfUnavailableError(f"perf stat failed:\n{result.stderr[-2000:]}")
    counts: dict[str, int] = {}
    for line in result.stderr.splitlines():
        fields = line.split(",")
        if len(fields) >= 3 and fields[0].strip().isdigit():
            counts[fields[2].strip()] = int(fields[0])
    return counts
