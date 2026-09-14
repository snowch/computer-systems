#!/usr/bin/env python3
"""The disassembly the book shows, captured from the compiler that produced it.

    python3 -m bench.run_disasm                  # both architectures
    python3 -m bench.run_disasm --arch riscv64   # one of them
    python3 -m bench.run_disasm --check          # regenerate and diff; write nothing

Every listing in the book comes from here. Chapters include a rendered fragment, so no machine
code is ever pasted into prose, and the compiler that emitted it is recorded beside it.

**This one runs in CI, and that is the interesting part.** Everything else the book measures
depends on a machine: a timing belongs to one board and CI cannot re-take it. A listing depends
on a compiler, and CI has the same compiler, so CI can regenerate every listing and diff it
against what is committed. The result is that the book's machine code is checked on every push in
a way its timings never can be.

``--check`` failing means one of two things, and both want the same fix. Either the source
changed and the listing was not re-rendered, or the toolchain moved under it and the compiler now
emits something else. The second is not a nuisance to be suppressed: a chapter discussing a
``csel`` that the reader's compiler no longer emits is a chapter that is wrong, and the whole
point of stamping is to find that out from CI rather than from a reader.
"""

from __future__ import annotations

import argparse
import difflib
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from bench.disasm import code_flags, disassemble
from bench.measure import HostTarget, ToolchainMissingError, flags_for
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    write_result,
)

#: The files whose functions the book reads as machine code: result stem -> (source, header,
#: symbols in the order a chapter meets them).
#:
#: One result per file per architecture rather than one big result, because the fingerprint is
#: taken over the sources a result names — so editing ch02's example would otherwise invalidate
#: ch01's listings and send an author to the wrong chapter looking for what changed.
SOURCES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "shapes": (
        "sysfs/lib/shapes.c",
        "sysfs/include/sysfs/shapes.h",
        ("sysfs_clamp", "sysfs_sum"),
    ),
    "addresses": (
        "sysfs/lib/addresses.c",
        "sysfs/include/sysfs/addresses.h",
        (
            "sysfs_read_four",
            "sysfs_read_four_volatile",
            "sysfs_sum_array",
            "sysfs_sum_pointer",
            "sysfs_uses_private",
            "sysfs_call_through",
        ),
    ),
    "pipeline": (
        "sysfs/lib/pipeline.c",
        "sysfs/include/sysfs/pipeline.h",
        (
            "sysfs_sum_chain1",
            "sysfs_sum_chain2",
            "sysfs_sum_chain4",
            "sysfs_sum_chain8",
            "sysfs_count_over",
            "sysfs_count_over_calling",
        ),
    ),
    "bridge": (
        "sysfs/lib/bridge.c",
        "sysfs/include/sysfs/bridge.h",
        ("sysfs_bridge_sequential", "sysfs_bridge_chased"),
    ),
    "ordering": (
        "sysfs/lib/ordering.c",
        "sysfs/include/sysfs/ordering.h",
        (
            "sysfs_bump_plain",
            "sysfs_bump_relaxed",
            "sysfs_bump_ordered",
            "sysfs_publish",
            "sysfs_publish_unordered",
        ),
    ),
    "frames": (
        "sysfs/lib/frames.c",
        "sysfs/include/sysfs/frames.h",
        ("sysfs_leaf", "sysfs_calls_out", "sysfs_accumulates"),
    ),
    "signedness": (
        "sysfs/lib/signedness.c",
        "sysfs/include/sysfs/signedness.h",
        (
            "sysfs_signed_grows",
            "sysfs_unsigned_grows",
            "sysfs_signed_quarter",
            "sysfs_unsigned_quarter",
        ),
    ),
    "stages": (
        "sysfs/lib/stages.c",
        "sysfs/include/sysfs/stages.h",
        ("sysfs_sum_folded", "sysfs_sum_counted"),
    ),
}

#: Which of the book's two worlds an instruction set belongs to.
#:
#: A listing was compiled, not executed, so ``target`` here does not say where anything ran — the
#: machine block says that, and says "nothing here was executed". What it says is which half of
#: the book the reader is in when they meet these instructions: RISC-V is the kernel they can stop
#: mid-trap, AArch64 is the machine whose counters work.
WORLD = {"riscv64": "xv6", "aarch64": "host"}

CROSS_PREFIX = {"riscv64": "riscv64-linux-gnu-", "aarch64": "aarch64-linux-gnu-"}

APT_PACKAGE = {"riscv64": "gcc-riscv64-linux-gnu", "aarch64": "gcc-aarch64-linux-gnu"}


def target_for(arch: str) -> HostTarget:
    """A compile-only target for one architecture.

    The cross compiler is preferred even on a machine that could compile natively, and the reason
    is reproducibility rather than convenience: listings are committed, so they should come from
    the toolchain CI also has. A Pi's own gcc is a different build of a different version, and
    letting ``make bench-listings`` on the board silently rewrite every listing in the book would
    make the committed ones depend on who ran the command last.
    """
    prefix = CROSS_PREFIX[arch]
    if shutil.which(f"{prefix}gcc"):
        cc = f"{prefix}gcc"
    elif platform.machine() == arch and shutil.which("gcc"):
        cc = "gcc"
    else:
        raise ToolchainMissingError(
            f"no {arch} compiler: install {APT_PACKAGE[arch]} (see ch00). Listings are committed, "
            "so this is only needed to regenerate them."
        )
    return HostTarget(
        name=f"listing-{arch}",
        cc=cc,
        flags=code_flags(flags_for(arch)),
        why=f"compiled for {arch} and disassembled; never executed",
    )


def capture(arch: str, stem: str = "shapes") -> dict[str, Any]:
    """Disassemble every symbol in one source file for one architecture, and stamp the lot."""
    source, header, symbols = SOURCES[stem]
    target = target_for(arch)
    listings = {}
    toolchain: dict[str, Any] = {}
    for symbol in symbols:
        listing = disassemble([source], symbol, target, includes=["sysfs/include"])
        if listing.arch != arch:
            raise RuntimeError(
                f"asked {target.cc} for {arch} and objdump read a {listing.arch} object file. "
                "A mismatched objdump decodes the wrong instruction set silently; fix the "
                "toolchain rather than the check."
            )
        listings[symbol] = listing.as_summary()
        # Same source, same flags, same compiler for every symbol, so the last one describes all
        # of them; the per-symbol objdump command is the only part that differs and it is
        # reconstructible from the symbol name.
        toolchain = dict(listing.toolchain)
    toolchain["objdump"] = toolchain["objdump"].split(" --disassemble=")[0] + " --disassemble=<fn>"

    return build_result(
        name=f"{stem}-{arch}",
        target=WORLD[arch],
        kind="listing",
        summary={"source": source, "listings": listings},
        code_sources=["bench/run_disasm.py", "bench/disasm.py", source, header],
        toolchain=toolchain | {"execution": "none — compiled to an object file and disassembled"},
        machine=describe_toolchain(arch),
        conditions={
            "note": "no timing: this records what the compiler chose, not what it cost",
            "compiler": compiler_version(target.cc),
        },
    )


def report_differences(fresh: dict[str, Any]) -> int:
    """Diff a fresh capture against what is committed, one listing at a time.

    Line by line rather than field by field. A listing is a paragraph of text, and being told that
    a forty-line string is "now" a different forty-line string identifies nothing — the useful
    output is the two instructions that changed.
    """
    name = fresh["name"]
    try:
        committed = load_result(name)
    except FileNotFoundError:
        print(f"{name}: nothing committed to compare against — run without --check first")
        return 1

    before = committed.get("summary", {}).get("listings", {})
    after = fresh["summary"]["listings"]
    changed = []

    for symbol in sorted(set(before) | set(after)):
        if symbol not in before:
            changed.append(f"  {symbol}: new, not in the committed result")
            continue
        if symbol not in after:
            changed.append(f"  {symbol}: gone from the capture, still in the committed result")
            continue
        diff = list(
            difflib.unified_diff(
                before[symbol]["text"].splitlines(),
                after[symbol]["text"].splitlines(),
                fromfile=f"{symbol} (committed)",
                tofile=f"{symbol} (now)",
                lineterm="",
            )
        )
        if diff:
            changed.append("\n".join(f"  {line}" for line in diff))

    if not changed:
        print(f"{name}: unchanged — this compiler still emits the instructions the book prints")
        return 0

    print(f"{name}: the compiler no longer emits what is committed\n")
    print("\n\n".join(changed))
    print(
        f"\nCommitted with: {committed.get('toolchain', {}).get('cc')}"
        f"\nRunning now:    {fresh['toolchain']['cc']}"
        "\n\nEither the source changed or the toolchain did. Both mean the listing in the book is "
        "no longer\nwhat this compiler produces, and both are fixed the same way:"
        "\n  python3 -m bench.run_disasm"
        "\n  python3 scripts/render-figures.py"
        "\nThen read the chapter around the listing: if the instructions moved, the prose about "
        "them may have to."
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch", choices=(*WORLD, "all"), default="all")
    parser.add_argument("--source", choices=(*SOURCES, "all"), default="all")
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate and diff against the committed listings; write nothing",
    )
    args = parser.parse_args(argv)

    arches = sorted(WORLD) if args.arch == "all" else [args.arch]
    stems = sorted(SOURCES) if args.source == "all" else [args.source]
    status = 0
    for stem in stems:
        for arch in arches:
            payload = capture(arch, stem)
            if args.check:
                status |= report_differences(payload)
            else:
                path = write_result(payload)
                listings = payload["summary"]["listings"]
                instructions = sum(entry["instructions"] for entry in listings.values())
                print(
                    f"wrote {Path(path).relative_to(ROOT)} "
                    f"({len(listings)} function(s), {instructions} instructions)"
                )
    return status


if __name__ == "__main__":
    sys.exit(main())
