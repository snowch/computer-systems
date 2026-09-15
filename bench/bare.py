"""Building and booting a program that has no operating system under it.

The ``bare`` target is the same processor ``xv6`` runs on, with everything else taken away: no
firmware, no kernel, no C library, no loader. QEMU is entered at the reset address with the
program already in memory, and the first instruction it executes is one this book wrote.

**Nothing here is ever timed**, for the reason ``xv6`` is never timed: QEMU models no cache, no
branch predictor, no store buffer and no memory latency. What it *is* exact about is semantics —
a trap lands where the vector register says it does, or it does not — and semantics is the whole
of what Part II asks about. ``bench.stamp.provenance_problems`` enforces this and CI runs it.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

from bench.stamp import ROOT

BARE_DIR = ROOT / "sysfs" / "bare"
BUILD_DIR = ROOT / "sysfs" / "build" / "bare"

CC = "riscv64-linux-gnu-gcc"
OBJDUMP = "riscv64-linux-gnu-objdump"

#: Every program links these. They are the whole of the runtime: an entry point that makes a
#: stack and zeroes the bss, and a console that puts bytes in a device register.
RUNTIME = ("start.S", "console.c")

#: Why each flag is here, because on this target a missing one does not produce an error — it
#: produces a machine that stops for a reason three layers away from the cause.
#:
#: ``-fno-pic`` is the one that cost an afternoon. Position-independent code reaches a global
#: through the global offset table, and on a machine with no loader nothing ever fills the global
#: offset table in: the handler address read out of it is zero, and the first trap jumps to zero.
CFLAGS = (
    "-march=rv64g",
    "-mabi=lp64",
    "-mcmodel=medany",  # the link address is above 2 GiB, out of reach of medlow's addressing
    "-ffreestanding",  # there is no hosted environment: no main() contract, no library
    "-nostdlib",  # and nothing to link against if there were
    "-fno-pic",  # see above: nothing fills a GOT here
    "-fno-stack-protector",  # the canary would come from a runtime that does not exist
    "-fno-builtin",  # so a memset() the compiler invented does not call a libc that is absent
    "-O1",
    "-g",
    "-Wall",
    "-Werror",
)


class BareUnavailableError(RuntimeError):
    """The bare target cannot run here: no cross compiler, or no QEMU."""


def problems() -> list[str]:
    missing = []
    if not shutil.which(CC):
        missing.append(f"{CC} is not installed (see ch00)")
    if not shutil.which("qemu-system-riscv64"):
        missing.append("qemu-system-riscv64 is not installed (see ch00)")
    return missing


def require_bare() -> None:
    if found := problems():
        raise BareUnavailableError("; ".join(found))


def sources_for(program: str) -> tuple[str, ...]:
    """The repo-relative sources of one program, runtime included.

    Every one of them goes into the result's fingerprint. A program is its own file *and* the
    entry code and console it was linked against, because a change to the stack layout in
    ``start.S`` can change what a program prints without its own source moving at all.
    """
    return tuple(f"sysfs/bare/{name}" for name in (*RUNTIME, f"{program}.c")) + (
        "sysfs/bare/bare.ld",
        "sysfs/bare/bare.h",
    )


def build(program: str) -> Path:
    """Compile and link one program into a flat image QEMU can be entered on."""
    require_bare()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    elf = BUILD_DIR / f"{program}.elf"
    command = [
        CC,
        *CFLAGS,
        "-T",
        str(BARE_DIR / "bare.ld"),
        "-o",
        str(elf),
        *[str(BARE_DIR / name) for name in RUNTIME],
        str(BARE_DIR / f"{program}.c"),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"building {program} failed:\n{result.stderr}")
    return elf


@dataclass
class BareRun:
    """What one program said before the machine stopped."""

    program: str
    output: str

    @property
    def lines(self) -> list[str]:
        return [line.strip() for line in self.output.splitlines() if line.strip()]

    def fields(self) -> dict[str, int]:
        """The ``<program> <name> <value>`` lines, as a dictionary.

        The programs print in this shape so that what a chapter quotes is parsed rather than
        scraped. A line that does not fit is not an error — the programs also print prose — it is
        simply not a field.
        """
        found: dict[str, int] = {}
        for line in self.lines:
            parts = line.split()
            if len(parts) == 3 and parts[0] == self.program:
                try:
                    found[parts[1]] = int(parts[2], 0)
                except ValueError:
                    continue
        return found


def run(program: str, *, harts: int = 1, timeout: int = 60) -> BareRun:
    """Boot one program and collect everything it printed.

    The program stops itself by writing the board's test finisher, so a run that reaches its end
    exits on its own. A run that does not is a hang — an unhandled trap looping on its own `mepc`
    is the usual cause — and the timeout is what turns that into a failed check rather than a CI
    job that never finishes.
    """
    elf = build(program)
    command = [
        "qemu-system-riscv64",
        "-machine",
        "virt",
        "-bios",
        "none",  # no OpenSBI: the program is the first thing that runs
        "-kernel",
        str(elf),
        "-m",
        "128M",
        "-smp",
        str(harts),
        "-nographic",
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        output, _ = process.communicate()
        raise RuntimeError(
            f"{program} did not stop within {timeout}s — it is looping. A handler that returns "
            f"without advancing mepc re-executes the instruction that trapped, for ever.\n"
            f"What it said first:\n{output}"
        ) from None

    sentinel = f"end {program}"
    if sentinel not in output:
        raise RuntimeError(
            f"{program} stopped without printing {sentinel!r}, so it did not reach its end.\n"
            f"Output:\n{output}"
        )
    return BareRun(program=program, output=output.split(sentinel)[0] + sentinel)


def disassemble(program: str, symbol: str) -> str:
    """One function of a built program, for a chapter that quotes instructions."""
    elf = build(program)
    result = subprocess.run(
        [OBJDUMP, "-d", "--no-show-raw-insn", f"--disassemble={symbol}", str(elf)],
        capture_output=True,
        text=True,
        check=True,
    )
    body = [line for line in result.stdout.splitlines() if line.strip()]
    start = next((i for i, line in enumerate(body) if line.endswith(f"<{symbol}>:")), 0)
    return "\n".join(body[start:])
