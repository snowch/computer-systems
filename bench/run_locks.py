#!/usr/bin/env python3
"""The locking chapter's artefact: what a lock is, in instructions, in the kernel as built.

    python3 -m bench.run_locks           # read the primitives out of the kernel and stamp them
    python3 -m bench.run_locks --check   # re-read and compare; write nothing

Not a measurement, and the reason is the chapter. What a lock *costs* is contention, contention is
a question about how long one core made another wait, and this target has no opinion about
duration — so a number here would describe the laptop. The false-sharing chapter prices contention
on hardware.

What is available, and is worth more than a fabricated timing, is what the primitives *are*. The
kernel is disassembled as built, so these are the instructions the machine actually runs rather
than a reimplementation written for a book. Two facts fall straight out and neither is obvious
from the C: acquiring is one atomic instruction, and releasing is a fence followed by an ordinary
store.
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
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

#: The four functions every critical section in xv6 passes through. Ordinary C functions with
#: sizes in the symbol table, so objdump can bound them by name — unlike the trap path's assembly labels.
PRIMITIVES = ("acquire", "release", "push_off", "pop_off")

#: RISC-V spells atomics and ordering distinctly enough to classify by mnemonic.
ATOMIC_PREFIXES = ("amo", "lr.", "sc.")


class LockReadError(RuntimeError):
    """The kernel does not contain the primitives this chapter is about."""


def classify(text: str) -> dict[str, Any]:
    """Count what the function is made of, by the only distinction that matters here."""
    body = [line.split(":\t", 1)[1] for line in text.splitlines() if ":\t" in line]
    mnemonics = [line.split()[0] for line in body if line.strip()]
    return {
        "instructions": len(mnemonics),
        "atomic": sum(1 for m in mnemonics if m.startswith(ATOMIC_PREFIXES)),
        "fences": sum(1 for m in mnemonics if m.startswith("fence")),
        "csr_operations": sum(1 for m in mnemonics if m.startswith("csr")),
        # An acquire spins; a release does not. The backward branch is how you tell without
        # reading the code, and it is the difference between waiting and not waiting.
        "branches": sum(1 for m in mnemonics if m.startswith(("b", "j")) and m != "jal"),
        "calls": sum(1 for m in mnemonics if m == "jal"),
    }


def read_primitives() -> dict[str, Any]:
    xv6.require()
    xv6.build()
    kernel = xv6.STAGE / "kernel" / "kernel"
    tool = objdump_for("riscv64-linux-gnu-gcc")

    out: dict[str, Any] = {}
    for symbol in PRIMITIVES:
        text = subprocess.run(
            [tool, "-d", "--no-show-raw-insn", f"--disassemble={symbol}", str(kernel)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        if f"<{symbol}>:" not in text:
            raise LockReadError(f"{symbol} is not in the built kernel")
        out[symbol] = classify(text)
    return out


def capture() -> dict[str, Any]:
    primitives = read_primitives()
    if primitives["acquire"]["atomic"] == 0:
        raise LockReadError(
            "acquire contains no atomic instruction, which cannot be a working lock. Either the "
            "kernel has changed or this is disassembling the wrong thing."
        )
    if primitives["release"]["fences"] == 0:
        raise LockReadError(
            "release contains no fence. On a weakly ordered machine that is a broken lock, so "
            "this is far likelier to be a bug in the measurement than a kernel that ships it."
        )
    return build_result(
        name="locks-xv6",
        target="xv6",
        kind="artefact",
        summary={"primitives": primitives},
        code_sources=["bench/run_locks.py", "bench/xv6.py"],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "none — the built kernel was read, not run",
        },
        machine=describe_toolchain("riscv64"),
        conditions={
            "note": "instruction counts only; contention is a duration and this target has none",
            "subject": "xv6's own spinlock, disassembled from the kernel as built",
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-read and compare; write nothing")
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
        print(f"{payload['name']}: unchanged — the lock is still made of these instructions")
        return 0
    print(f"{payload['name']}: the lock primitives have MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print("\nRe-run and commit:\n  python3 -m bench.run_locks\n  python3 scripts/render-figures.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
