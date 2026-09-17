#!/usr/bin/env python3
"""The machine-code chapter's artefact: what the stack frame costs, at two optimisation levels.

    python3 -m bench.run_frames           # measure and stamp
    python3 -m bench.run_frames --check   # re-measure and compare; write nothing

Not a timing. A frame size is a count of bytes the prologue subtracts from the stack pointer, and
an instruction mix is a count of instructions by kind — both read straight out of the
disassembly, both reproducible anywhere the compiler is, and both stamped ``kind: artefact``.

The interesting column is the comparison. The same four functions are compiled at ``-O0`` and at
``-O2``, and the difference between the two frames is the clearest statement available of what an
optimiser is actually *for*: it is not making the arithmetic cleverer, it is keeping values in
registers instead of in memory.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from bench.disasm import disassemble
from bench.measure import HostTarget, flags_for
from bench.run_disasm import CROSS_PREFIX, target_for
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

SOURCE = "sysfs/lib/frames.c"
HEADER = "sysfs/include/sysfs/frames.h"
SYMBOLS = ("sysfs_leaf", "sysfs_calls_out", "sysfs_many_locals", "sysfs_accumulates")
ARCH = "riscv64"

#: The prologue's own statement of how much stack it wants. RISC-V spells it as an immediate
#: subtracted from the stack pointer, and a function that needs no stack does not spell it at all.
_FRAME = re.compile(r"addi\s+sp,sp,(-\d+)")

#: Instructions grouped by what they do to the machine, which is the grouping that says something
#: about a function. Matched on the mnemonic's shape rather than an exhaustive list, because the
#: list is long and the shapes are stable: RISC-V loads start `l`, stores start `s`.
_KINDS = {
    "load": re.compile(r"^l[bhwd]u?$|^lr\."),
    "store": re.compile(r"^s[bhwd]$|^sc\."),
    "branch": re.compile(r"^b(eq|ne|lt|ge|ltu|geu)z?$|^j$|^jr$"),
    "call": re.compile(r"^jal$|^jalr$|^call$|^tail$"),
}


def _mnemonics(listing: str) -> list[str]:
    out = []
    for line in listing.splitlines():
        if ":\t" not in line:
            continue
        body = line.split(":\t", 1)[1].strip()
        out.append(body.split()[0] if body else "")
    return out


def measure(symbol: str, level: str) -> dict[str, Any]:
    """Frame size and instruction mix for one function at one optimisation level."""
    base = target_for(ARCH)
    flags = tuple(f for f in flags_for(ARCH) if not f.startswith("-O")) + (level,)
    target = HostTarget(name=f"framesizes-{ARCH}", cc=base.cc, flags=flags)
    listing = disassemble([SOURCE], symbol, target, includes=["sysfs/include"])

    frame = _FRAME.search(listing.text)
    mix = dict.fromkeys(_KINDS, 0)
    for mnemonic in _mnemonics(listing.text):
        for kind, pattern in _KINDS.items():
            if pattern.match(mnemonic):
                mix[kind] += 1
                break

    return {
        "symbol": symbol,
        "level": level,
        "instructions": listing.instructions,
        "frame_bytes": -int(frame.group(1)) if frame else 0,
        **mix,
    }


def capture() -> dict[str, Any]:
    rows = [measure(symbol, level) for symbol in SYMBOLS for level in ("-O0", "-O2")]
    cc = f"{CROSS_PREFIX[ARCH]}gcc"
    return build_result(
        name=f"framesizes-{ARCH}",
        target="xv6",
        kind="artefact",
        summary={"source": SOURCE, "functions": rows},
        code_sources=["bench/run_frames.py", "bench/disasm.py", SOURCE, HEADER],
        toolchain={
            "cc": compiler_version(cc),
            "flags": "-Wall -Wextra -march=rv64gc -mabi=lp64d -c, at -O0 and -O2",
            "execution": "none — compiled twice and disassembled",
        },
        machine=describe_toolchain(ARCH),
        conditions={
            "note": "counts of instructions and stack bytes; nothing was executed or timed",
            "frame_bytes": "read from the prologue's own `addi sp,sp,-N`; 0 means no frame",
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-measure and compare")
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
        print(f"{payload['name']}: unchanged — the compiler still builds these frames")
        return 0
    print(f"{payload['name']}: the frames have MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_frames\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
