#!/usr/bin/env python3
"""Chapter 6's measurement: how often the kernel is entered, why, and how far it has to go.

    python3 -m bench.run_traps           # boot, run the workload, read the census
    python3 -m bench.run_traps --check   # re-run and compare; write nothing

Two kinds of fact, neither of them a duration.

**The census** comes from the kernel itself. ``xv6/patches/06-trap-census.patch`` counts every
trap by cause and prints the table on Ctrl-T, the way xv6 already prints its process table on
Ctrl-P. Counting is what is available here: QEMU models no pipeline and no memory system, so a
time measured inside it describes the laptop, and ch06 says so at length.

**The path length** is read out of the built kernel. Entering and leaving the kernel is a fixed
sequence of instructions in ``trampoline.S``, and counting them is a statement about how much
work a trap *is* that holds regardless of what any machine charges for it. ch19 puts a price on
the same path, on hardware.
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

#: The workload: a program that asks for one thing a known number of times.
#:
#: Counting the shell was the obvious first try and it does not work. How many times the shell
#: calls `read` depends on how the console delivered its characters, which depends on timing,
#: which inside QEMU is a property of the laptop — two runs of the identical workload disagreed,
#: which is how this was found. `trapload` removes the question: nothing else in the system calls
#: `getpid`, so that entry in the census is a number this program decided.
WORKLOAD = ["trapload"]

#: What `trapload` asks for, and how many times. Kept in step with the program by a test.
PROBE_SYSCALL = 11  # getpid
PROBE_CALLS = 1000

#: Ctrl-T, which the patch binds to printing the census.
DUMP = "\x14"

#: The two halves of the trap path, both in trampoline.S: the way in and the way out.
PATH_SYMBOLS = ("uservec", "userret")


class CensusError(RuntimeError):
    """The kernel did not print a census."""


def read_census(transcript: str) -> dict[str, Any]:
    totals: dict[str, int] = {}
    exceptions: dict[str, int] = {}
    interrupts: dict[str, int] = {}
    syscalls: dict[str, int] = {}
    complete = False
    for raw in transcript.splitlines():
        # The first census line lands on the same line as the shell prompt that was waiting for
        # input when Ctrl-T arrived, so the marker is found rather than assumed to start the line.
        if "end trapcensus" in raw:
            complete = True
            continue
        marker = raw.find("trapcensus ")
        if marker < 0:
            continue
        parts = raw[marker:].split()
        match parts[1:]:
            case ["user", user, "kernel", kernel, "unclassified", other]:
                totals = {
                    "from_user": int(user),
                    "from_kernel": int(kernel),
                    "unclassified": int(other),
                }
            case ["exception", code, count]:
                exceptions[code] = int(count)
            case ["interrupt", code, count]:
                interrupts[code] = int(count)
            case ["syscall", number, count]:
                syscalls[number] = int(count)
    if not complete or not totals:
        raise CensusError(f"no census in the transcript:\n{transcript[-2000:]}")

    # Only what the workload decided is recorded as a number, and the rest as a list of what
    # occurred. The distinction is not fastidiousness — it is the difference between a figure that
    # means something and one that moves when the laptop is busy.
    #
    # `trapload` asks for one thing a fixed number of times, so that entry is reproducible on any
    # machine. Everything else in the census is the shell going about its business: how many times
    # it read the console depends on how the console delivered characters, and how many times a
    # device interrupted depends on how long that took. Those counts differ between two runs of
    # the identical workload — which is how this was found out, rather than assumed.
    #
    # Even a count of *how many distinct* calls the run used is unsafe, and was tried: the shell
    # occasionally makes one it otherwise does not, so the number moved between two runs of the
    # same workload. What survives here is a number the workload fixed and lists of what occurred.
    #
    # ch19 counts the lot, on a machine where elapsed time is a fact about the machine.
    probe = syscalls.get(str(PROBE_SYSCALL), 0)
    return {
        "probe_syscall": PROBE_SYSCALL,
        "probe_calls_counted": probe,
        "exception_causes_seen": sorted(int(code) for code in exceptions),
        "interrupt_causes_seen": sorted(int(code) for code in interrupts),
    }


def _symbol_addresses(kernel: Path) -> dict[str, int]:
    tool = objdump_for("riscv64-linux-gnu-gcc").replace("objdump", "nm")
    printed = subprocess.run([tool, str(kernel)], capture_output=True, text=True, check=True).stdout
    out: dict[str, int] = {}
    for line in printed.splitlines():
        parts = line.split()
        if len(parts) == 3:
            out[parts[2]] = int(parts[0], 16)
    return out


def measure_path() -> dict[str, Any]:
    """How many instructions the way in and the way out contain, and how much state they move.

    Measured by address range rather than by symbol, which is not fussiness. ``uservec`` is an
    assembly label: the assembler gave it no size, and it shares its address with ``trampoline``,
    so asking objdump to disassemble it by name produces nothing at all — silently. The addresses
    come from the symbol table and the extent of each half is the distance to the next label,
    which is exactly how the trampoline page is laid out.
    """
    kernel = xv6.STAGE / "kernel" / "kernel"
    addresses = _symbol_addresses(kernel)
    tool = objdump_for("riscv64-linux-gnu-gcc")

    #: The trampoline is one page, entered at the top and left from `userret`.
    bounds = {
        "uservec": (addresses["uservec"], addresses["userret"]),
        "userret": (addresses["userret"], addresses["trampoline"] + 4096),
    }

    path: dict[str, Any] = {}
    for name, (start, stop) in bounds.items():
        text = subprocess.run(
            [
                tool,
                "-d",
                "--no-show-raw-insn",
                f"--start-address={start:#x}",
                f"--stop-address={stop:#x}",
                str(kernel),
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        body = [line for line in text.splitlines() if ":\t" in line]
        mnemonics = [
            line.split(":\t", 1)[1].split()[0] for line in body if line.split(":\t", 1)[1].strip()
        ]
        # The page is padded to its end with zeros, which disassemble as `unimp`. They are not
        # part of the path and counting them would make the way out look twice as long as it is.
        mnemonics = [m for m in mnemonics if m != "unimp"]
        path[name] = {
            "instructions": len(mnemonics),
            "register_stores": sum(1 for m in mnemonics if m == "sd"),
            "register_loads": sum(1 for m in mnemonics if m == "ld"),
            "csr_operations": sum(1 for m in mnemonics if m.startswith("csr")),
        }
    return path


def capture() -> dict[str, Any]:
    xv6.require()
    result = xv6.boot([*WORKLOAD, DUMP])
    if result.timed_out:
        raise CensusError(f"xv6 did not finish the workload:\n{result.transcript[-2000:]}")
    census = read_census(result.transcript)
    if census["probe_calls_counted"] != PROBE_CALLS:
        raise CensusError(
            f"trapload asked for {PROBE_CALLS} and the kernel counted "
            f"{census['probe_calls_counted']}. Either the program or the patch has changed."
        )
    summary = {"census": census, "path": measure_path(), "workload": WORKLOAD}
    return build_result(
        name="traps-xv6",
        target="xv6",
        summary=summary,
        code_sources=[
            "bench/run_traps.py",
            "bench/xv6.py",
            "xv6/apps/trapload.c",
            "xv6/patches/06-trap-census.patch",
        ],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "qemu-system-riscv64 -machine virt",
        },
        machine=describe_qemu(),
        conditions={
            "cpus": xv6.DEFAULT_CPUS,
            "note": "counts only — QEMU models no timing, so none is recorded (ch00)",
            "workload": " ; ".join(WORKLOAD),
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
        print(f"{payload['name']}: unchanged — the same workload still takes the same traps")
        return 0
    print(f"{payload['name']}: the census has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print("\nRe-run and commit:\n  python3 -m bench.run_traps\n  python3 scripts/render-figures.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
