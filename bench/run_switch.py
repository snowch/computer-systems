#!/usr/bin/env python3
"""The scheduling chapter's measurement: what a context switch moves, and how many of them a workload decides.

    python3 -m bench.run_switch           # read swtch out of the kernel, boot, read the census
    python3 -m bench.run_switch --check   # re-run and compare; write nothing

Two facts, and the first is the chapter.

**What `swtch` saves**, read out of the kernel as built. A context switch is a function call, so
the ABI has already dealt with everything a caller was willing to lose — which means the switch
itself has to preserve far less than the traps chapter's trap path, and the difference is not an optimisation
but a consequence of one side having agreed to the convention.

**How many switches a workload causes**, by reason. Only one of the three reasons is a number the
workload fixes: a process that exits switches away exactly once. How often the timer took the CPU
away is a statement about elapsed time, and how often a process waited is a statement about
whether the thing it waited for had already happened — so those two are counted by the kernel and
declined by this runner, for the drivers chapter's reasons.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from bench import xv6
from bench.disasm import objdump_for
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_qemu,
    load_result,
    measurement_differences,
    write_result,
)

WORKLOAD = ["switchload"]
PATCH = "xv6/patches/18-switch-census.patch"
APP = "xv6/apps/switchload.c"

#: Ctrl-X, which the patch binds to printing the census.
DUMP = "\x18"

#: Every register is eight bytes on RV64.
REGISTER_BYTES = 8


class SwitchError(RuntimeError):
    """The kernel did not switch the way this chapter says it does."""


def measure_swtch() -> dict[str, Any]:
    """What the switch moves, counted from the instructions that move it."""
    xv6.require()
    xv6.build()
    kernel = xv6.STAGE / "kernel" / "kernel"
    tool = objdump_for("riscv64-linux-gnu-gcc")
    text = subprocess.run(
        [tool, "-d", "--no-show-raw-insn", "--disassemble=swtch", str(kernel)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if "<swtch>:" not in text:
        raise SwitchError("swtch is not in the built kernel")

    mnemonics = [
        line.split(":\t", 1)[1].split()[0]
        for line in text.splitlines()
        if ":\t" in line and line.split(":\t", 1)[1].strip()
    ]
    saved = sum(1 for m in mnemonics if m == "sd")
    restored = sum(1 for m in mnemonics if m == "ld")
    if saved != restored:
        raise SwitchError(
            f"swtch saves {saved} registers and restores {restored}. A switch that does not put "
            "back what it took is not a switch, so this is a bug in the measurement or in xv6."
        )
    return {
        "instructions": len(mnemonics),
        "registers_saved": saved,
        "registers_restored": restored,
        "bytes_moved": (saved + restored) * REGISTER_BYTES,
    }


def read_census(transcript: str) -> dict[str, Any]:
    counted: dict[str, int] = {}
    declared: dict[str, int] = {}
    complete = False
    for raw in transcript.splitlines():
        if "end switchcensus" in raw:
            complete = True
            continue
        marker = raw.find("switchload children ")
        if marker >= 0:
            declared["children"] = int(raw[marker:].split()[2])
            continue
        marker = raw.find("switchcensus total ")
        if marker < 0:
            continue
        parts = raw[marker:].split()
        counted = {
            "total": int(parts[2]),
            "by_yield": int(parts[4]),
            "by_sleep": int(parts[6]),
            "by_exit": int(parts[8]),
        }
    if not complete or not counted or not declared:
        raise SwitchError(f"no usable switch census in the transcript:\n{transcript[-2000:]}")
    return {"counted": counted, "declared": declared}


def believe(census: dict[str, Any]) -> dict[str, Any]:
    """Keep the one count the workload decided, and say which were declined."""
    counted, declared = census["counted"], census["declared"]
    children = declared["children"]
    if counted["by_exit"] < children:
        raise SwitchError(
            f"{children} children exited and the kernel counted {counted['by_exit']} switches out "
            "of an exiting process. Either the program or the patch has changed."
        )
    return {
        "children_created": children,
        "switches_out_of_an_exiting_process": counted["by_exit"],
        "counts_not_recorded": ["by_yield", "by_sleep"],
    }


def capture() -> dict[str, Any]:
    swtch = measure_swtch()
    result = xv6.boot([*WORKLOAD, DUMP])
    if result.timed_out:
        raise SwitchError(f"xv6 did not finish the workload:\n{result.transcript[-2000:]}")
    return build_result(
        name="switch-xv6",
        target="xv6",
        summary={"swtch": swtch, "census": believe(read_census(result.transcript))},
        code_sources=["bench/run_switch.py", "bench/xv6.py", APP, PATCH],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "qemu-system-riscv64 -machine virt",
        },
        machine=describe_qemu(),
        conditions={
            "cpus": xv6.DEFAULT_CPUS,
            "note": "counts and register widths only; a switch is never timed on this target",
            "omitted": "switches caused by the timer or by waiting, which measure elapsed time",
        },
    )


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
        print(f"{payload['name']}: unchanged — a switch still moves this much")
        return 0
    print(f"{payload['name']}: the switch census has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_switch\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
