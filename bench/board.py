"""The plumbing every board measurement shares, so that twelve runners are not twelve policies.

    from bench.board import require_board, timed_run, stamp_timing

Each `host` result in Part V answers a different question, but the way it is obtained is the same
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
import tempfile
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
    extra_flags: list[str] | None = None,
) -> str:
    """Build a workload against the book's clock and run it, returning what it printed.

    Every workload links `sysfs/lib/timing.c`, because every duration in Part V is read through
    the one clock ch21 built and argued about. A runner that timed with its own `clock_gettime`
    would be a second, unexamined instrument.

    `extra_flags` is appended, not substituted, so ch28 can build one source twice — once as the
    reader's own `-O2` would and once with the level that lets this compiler widen a loop — with
    everything else about the two builds identical.
    """
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    target = (
        NATIVE
        if not extra_flags
        else HostTarget(
            name=f"{NATIVE.name}{''.join(extra_flags)}",
            cc=NATIVE.cc,
            flags=(*NATIVE.flags, *extra_flags),
            trustworthy_for_timing=True,
            why=NATIVE.why,
        )
    )
    built = compile_program(
        [*sources, "sysfs/lib/timing.c"],
        build_dir / name,
        target,
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


def require_perf_sampling(what: str) -> None:
    """Counting and sampling are different permissions and different hardware.

    `perf stat` needs a counter; `perf record` needs that counter to raise an interrupt when it
    overflows, which is the capability ch27's header says most affordable RISC-V cores lack and
    ARM PMUs have as standard. A kernel can also be configured to allow one and not the other, so
    this probes sampling specifically rather than assuming that working counters imply it.
    """
    require_perf(what)
    with tempfile.TemporaryDirectory() as scratch:
        recording = Path(scratch) / "probe.data"
        result = subprocess.run(
            ["perf", "record", "-q", "-o", str(recording), "--", "sleep", "0.2"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not recording.exists():
            last = result.stderr.strip().splitlines()
            raise PerfUnavailableError(
                f"{what} needs perf to *sample*, and this machine would not.\n"
                "  sudo sysctl kernel.perf_event_paranoid=1\n"
                "If that does not help, this core's PMU may not raise an interrupt on counter "
                "overflow, which ch27's header names as the one thing it cannot work around.\n"
                f"perf said: {last[-1] if last else 'nothing'}"
            )


def perf_record(recording: Path, command: list[str], frequency: int = 999) -> None:
    """Sample `command` into `recording`.

    The frequency is not a round number on purpose. ch27's third problem is about a fixed sampling
    period aliasing against a loop of fixed length, and 999 rather than 1000 is the smallest
    possible acknowledgement that the problem is real — real profilers also jitter the period,
    which perf does by default.
    """
    result = subprocess.run(
        [
            "perf",
            "record",
            "-q",
            "-F",
            str(frequency),
            "--call-graph",
            "none",
            "-o",
            str(recording),
            "--",
            *command,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PerfUnavailableError(f"perf record failed:\n{result.stderr[-2000:]}")


def perf_report(recording: Path) -> list[tuple[float, str]]:
    """Read a recording back as (percentage, symbol), heaviest first."""
    result = subprocess.run(
        [
            "perf",
            "report",
            "-i",
            str(recording),
            "--stdio",
            "-q",
            "--no-children",
            "--percent-limit",
            "0.1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PerfUnavailableError(f"perf report failed:\n{result.stderr[-2000:]}")
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[0].endswith("%"):
            try:
                rows.append((float(fields[0].rstrip("%")), fields[-1]))
            except ValueError:
                continue
    return rows


def perf_annotate(recording: Path, symbol: str) -> list[tuple[float, str]]:
    """Per-instruction samples for one symbol, as (percentage, instruction text)."""
    result = subprocess.run(
        ["perf", "annotate", "-i", str(recording), "--stdio", "-s", symbol, "--no-source"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PerfUnavailableError(f"perf annotate failed:\n{result.stderr[-2000:]}")
    rows = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        head = stripped.split(":", 1)[0].strip()
        try:
            percent = float(head)
        except ValueError:
            continue
        rows.append((percent, stripped.split(":", 1)[1].strip()))
    return rows
