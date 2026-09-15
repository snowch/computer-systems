#!/usr/bin/env python3
"""Chapter 0's measurements: prove each target works, and record exactly what it is.

    python3 -m bench.run_setup --target xv6             # boots xv6 under QEMU; runs anywhere
    python3 -m bench.run_setup --target host            # the board's own account of itself
    python3 -m bench.run_setup --target xv6 --check     # re-measure and compare; write nothing

Neither of these is a timing measurement, which is why the ``xv6`` half can run in CI. They are
the two facts every later chapter depends on: that the toolchain produces working RV64 code, and
that the machine the book claims to have measured is the machine it says it is.

``--check`` re-measures and compares against the committed result without writing anything. CI
runs it on every push, because it closes a hole nothing else covers: ``verify-numbers.py`` hashes
the *files* a result names, and the xv6 submodule commit is not a file. Bumping the submodule, or
adding a kernel patch, can therefore change what the kernel reports while every fingerprint still
matches. Re-running the measurement is the only thing that notices.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from bench import xv6
from bench.measure import compile_program, resolve_host_target
from bench.stamp import (
    ROOT,
    build_result,
    classify_machine,
    compiler_version,
    describe_board,
    describe_qemu,
    flags_string,
    load_result,
    measurement_differences,
    write_result,
)

#: The probe's source. Both targets compile these same bytes; only the printf differs.
PROBE_HEADER = "sysfs/include/sysfs/probe.h"
HOST_PROBE = "sysfs/tools/sysprobe.c"
XV6_PROBE = "xv6/apps/sysprobe.c"

BUILD_DIR = ROOT / "sysfs" / "build"


class ProbeError(RuntimeError):
    """The probe did not say what a probe is supposed to say."""


def parse_probe(text: str) -> dict[str, Any]:
    """Turn the probe's key/value lines into a summary, and refuse anything truncated.

    The ``end sysprobe`` sentinel matters more than it looks. Reading from an emulated serial
    console is reading from a pipe that can be cut off mid-line, and a silently truncated table
    of type sizes would be a wrong number in the book rather than a failed run.
    """
    types: list[dict[str, Any]] = []
    layouts: list[dict[str, Any]] = []
    offsets: dict[str, int] = {}
    endian = world = None
    complete = False

    for raw in text.splitlines():
        parts = raw.strip().split()
        if not parts:
            continue
        match parts:
            case ["type", name, size, align]:
                types.append({"name": name, "size": int(size), "align": int(align)})
            case ["layout", name, size, align, padding]:
                layouts.append(
                    {
                        "name": name,
                        "size": int(size),
                        "align": int(align),
                        "padding": int(padding),
                    }
                )
            case ["offset", member, value]:
                offsets[member] = int(value)
            case ["endian", value]:
                endian = value
            case ["world", value]:
                world = value
            case ["end", "sysprobe"]:
                complete = True

    if not complete:
        raise ProbeError(f"probe output was truncated; got:\n{text}")
    if not types or not layouts or endian is None or world is None:
        raise ProbeError(f"probe output was incomplete; got:\n{text}")

    return {
        "world": world,
        "types": types,
        "layouts": layouts,
        "offsets": offsets,
        "endian": endian,
    }


# -- the xv6 target ----------------------------------------------------------------------


def run_xv6() -> dict[str, Any]:
    """Boot xv6, ask it the probe's questions, and count what booted."""
    xv6.require()
    result = xv6.boot(["sysprobe", "ls"])
    if result.timed_out:
        raise RuntimeError(f"xv6 did not reach a usable shell:\n{result.transcript[-2000:]}")

    summary = parse_probe(result.output_of("sysprobe"))
    if summary["world"] != "xv6":
        raise ProbeError(f"expected the xv6 build of the probe, got {summary['world']!r}")

    listing = [line for line in result.output_of("ls").splitlines() if line.strip()]
    kernel = xv6.STAGE / "kernel" / "kernel"

    summary |= {
        # Every hart announces itself on the way up. Counting the announcements is a statement
        # about what actually started, not about what -smp asked for.
        "harts": len(re.findall(r"hart \d+ starting", result.transcript)) + 1,
        "cpus_requested": result.cpus,
        # Two entries in any xv6 listing are "." and "..", and one is the console device.
        "user_programs": sum(
            1 for line in listing if line.split()[0] not in {".", "..", "console", "README"}
        ),
        "kernel_bytes": kernel.stat().st_size,
    }
    return summary


# -- the host target ---------------------------------------------------------------------


def perf_capability() -> dict[str, Any]:
    """Whether ``perf stat`` on this board reads real hardware counters, and which ones.

    This is the single most important thing chapter 0 establishes about the board, because every
    chapter in Part V assumes it. On RISC-V the counters reach Linux through the SBI PMU
    extension, so the answer depends on the firmware as much as on the silicon — which means it
    has to be asked of the machine rather than looked up.

    ``<not supported>`` and ``<not counted>`` are perf's way of saying the event did not reach
    hardware. Treating a zero as a reading is how a chapter ends up asserting that a loop
    retired no instructions.
    """
    if not shutil.which("perf"):
        return {
            "perf_counters_readable": False,
            "perf_note": "perf is not installed (linux-tools; see ch00)",
        }

    probe = subprocess.run(
        ["perf", "stat", "-x,", "-e", "cycles,instructions", "--", "true"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = probe.stderr + probe.stdout
    counted: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split(",")
        if len(fields) >= 3 and fields[0].strip().isdigit():
            counted[fields[2].strip()] = int(fields[0])

    readable = bool(counted) and all(value > 0 for value in counted.values())
    events = subprocess.run(
        ["perf", "list", "hw", "cache"], capture_output=True, text=True, check=False
    ).stdout
    hardware_events = sorted(
        {
            match.group(1)
            for match in re.finditer(r"^\s{2}([\w\-\.]+)\s+\[Hardware", events, re.MULTILINE)
        }
    )

    return {
        "perf_counters_readable": readable,
        "perf_cycles_event": next((k for k in counted if k.startswith("cycles")), None),
        "perf_counts": counted,
        "perf_hardware_events": hardware_events,
        "perf_note": None if readable else "perf ran but no event reached hardware",
        **perf_can_sample(),
    }


#: A workload that is on-CPU for long enough to be sampled, using only the interpreter already
#: running this. The choice matters more than it looks: ``perf record -- sleep 2`` is the obvious
#: test and it is wrong, because a sleeping task retires no instructions and burns no cycles, so
#: a perfectly working PMU returns nothing and the board is declared incapable.
_SPIN = "x = 0\nfor _ in range(4_000_000):\n    x += 1\n"

#: perf's own count of what it collected, from ``perf report --stats``.
_SAMPLE_COUNT = re.compile(r"SAMPLE events:\s+(\d+)")


def perf_can_sample() -> dict[str, Any]:
    """Whether ``perf record`` can sample on this board, which is a separate question.

    Counting and sampling are different capabilities and a board can have the first without the
    second. Sampling needs the counters to raise an overflow interrupt, which on RISC-V means the
    **Sscofpmf** extension @riscv-sscofpmf; a kernel without it says so at boot and then refuses.
    The SiFive U74 does not implement it. That is the difference between ch26, which counts, and
    ch27, which samples, so it is recorded as a fact about the board rather than discovered in a
    chapter.

    **This asks for samples rather than for an exit code.** An earlier version ran
    ``perf record -- true`` and believed a zero return, which is the same mistake as believing a
    counter that reads zero: ``perf`` will open the event, collect nothing from a program that
    barely runs, and exit successfully. The question is not whether the command succeeded, it is
    whether any samples came back — so this spins deliberately and counts them.
    """
    if not shutil.which("perf"):
        return {"perf_can_sample": False, "perf_samples": 0}

    with tempfile.TemporaryDirectory() as scratch:
        data = Path(scratch) / "perf.data"
        record = subprocess.run(
            ["perf", "record", "-F", "999", "-e", "cycles", "-o", str(data), "--"]
            + [sys.executable, "-c", _SPIN],
            capture_output=True,
            text=True,
            check=False,
        )
        noise = (record.stderr + record.stdout).lower()
        if "not supported" in noise or not data.exists():
            return {"perf_can_sample": False, "perf_samples": 0}

        stats = subprocess.run(
            ["perf", "report", "--stats", "-i", str(data)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        found = _SAMPLE_COUNT.search(stats)
        samples = int(found.group(1)) if found else 0

    return {"perf_can_sample": samples > 0, "perf_samples": samples}


def run_host() -> dict[str, Any]:
    """Describe the board, and prove its native toolchain builds and runs RV64 code.

    Refuses to run anywhere else. A ``host`` result is a claim about one specific machine, and
    the most useful thing this function does is decline to produce one from a laptop.
    """
    kind = classify_machine()
    if kind != "board":
        raise SystemExit(
            f"--target host describes the machine being measured, and this is a {kind!r} one.\n"
            "Run it over SSH on the machine being measured:  make bench-board\n"
            "Nothing here can be measured by emulation; see ch00 for why."
        )

    target = resolve_host_target()
    built = compile_program(
        [HOST_PROBE], BUILD_DIR / "sysprobe", target, includes=["sysfs/include"]
    )
    summary = parse_probe(built.run().stdout)
    if summary["world"] != "host":
        raise ProbeError(f"expected the host build of the probe, got {summary['world']!r}")

    summary |= {
        "native_cc": compiler_version(target.cc),
        "native_flags": flags_string(target.flags),
    }
    summary |= perf_capability()
    return summary


# -- entry point -------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("host", "xv6"), required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-measure and compare against the committed result; write nothing",
    )
    args = parser.parse_args(argv)

    if args.target == "xv6":
        summary = run_xv6()
        payload = build_result(
            name="setup-xv6",
            target="xv6",
            summary=summary,
            code_sources=["bench/run_setup.py", "bench/xv6.py", XV6_PROBE, PROBE_HEADER],
            toolchain={
                "cc": compiler_version("riscv64-linux-gnu-gcc"),
                "flags": "xv6's own CFLAGS (-O -march=rv64gc -std=gnu99 -ffreestanding)",
                "execution": "qemu-system-riscv64 -machine virt",
            },
            machine=describe_qemu(),
            conditions={
                "cpus": summary["cpus_requested"],
                "memory": "128M",
                "note": "structural facts only — QEMU models no timing (ch00)",
            },
        )
    else:
        summary = run_host()
        target = resolve_host_target()
        payload = build_result(
            name="setup-host",
            target="host",
            summary=summary,
            code_sources=["bench/run_setup.py", HOST_PROBE, PROBE_HEADER],
            toolchain=target.stamp(),
            machine=describe_board(),
            conditions={"note": "identity and capability, measured natively on the board"},
        )

    if args.check:
        return report_differences(payload)

    path = write_result(payload)
    print(f"wrote {Path(path).relative_to(ROOT)}")
    return 0


def report_differences(fresh: dict[str, Any]) -> int:
    """Compare a fresh run against what is committed, and say what moved."""
    name = fresh["name"]
    try:
        committed = load_result(name)
    except FileNotFoundError:
        print(f"{name}: nothing committed to compare against — run without --check first")
        return 1

    differences = measurement_differences(committed, fresh)
    if not differences:
        print(f"{name}: unchanged — a fresh run still gives the answers that are committed")
        return 0

    print(f"{name}: the measurement has MOVED since it was committed\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nThe committed result is stale, so any table rendered from it is showing a figure the "
        "code no longer produces.\nRe-run and commit:\n"
        f"  python3 -m bench.run_setup --target {fresh['target']}\n"
        "  python3 scripts/render-figures.py\n"
        "Whether the cause is a submodule bump, a new patch or a different compiler, the fix is "
        "the same."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
