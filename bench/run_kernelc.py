#!/usr/bin/env python3
"""The freestanding-C chapter's census: what the kernel as built does not have.

    python3 -m bench.run_kernelc           # walk the built kernel and stamp what is there
    python3 -m bench.run_kernelc --check    # re-walk and compare; write nothing

It tells a reader who already writes C which of their habits stop working below the library.
Every one of those claims is checkable against the kernel that is checked in, so none of them is
asserted here: the floating-point instruction count, the absence of a heap, the library functions
the kernel reimplements because nothing supplies them, and the compile-time bounds that stand in
for allocation are all read out of the binary and the source at its pinned commit.

Counted rather than timed, so it belongs to the `xv6` target and needs no board — and CI can
regenerate it, which is the point. A chapter whose argument is "the kernel has no floating point"
should fail when a kernel acquires some.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from bench import xv6
from bench.stamp import (
    ROOT,
    build_result,
    load_result,
    measurement_differences,
    write_result,
    xv6_commit,
)

#: Files whose job is to supply what a hosted C program gets from its library.
LIBRARY_SOURCES = ("string.c", "printk.c")

#: What a hosted program would call instead of writing its own.
HEAP_FUNCTIONS = ("malloc", "free", "calloc", "realloc")

#: A floating-point *register* operand, which is unambiguous. Matching mnemonics that start with
#: `f` is not: `fence` is an ordering instruction and appears in every lock in the kernel.
FP_OPERAND = re.compile(r"\bf[tsa]\d+\b")

#: An instruction line in objdump's output: an address, a colon, then the mnemonic.
INSTRUCTION = re.compile(r"^\s+[0-9a-f]+:\s")

#: A definition in xv6's house style, where the return type is on its own line above the name.
DEFINITION = re.compile(r"^([a-z_][a-z0-9_]*)\(", re.MULTILINE)

#: The compile-time bounds that are this kernel's allocator. Every one of them is the size of an
#: array that exists for the whole run, because there is nothing to allocate from.
POOL_BOUNDS = ("NPROC", "NCPU", "NOFILE", "NFILE", "NINODE", "NDEV", "NBUF", "MAXARG")


class KernelCError(RuntimeError):
    """The kernel stopped being the kernel the chapter describes."""


def toolprefix() -> str:
    for prefix in ("riscv64-linux-gnu-", "riscv64-unknown-elf-"):
        if subprocess.run(["which", f"{prefix}objdump"], capture_output=True).returncode == 0:
            return prefix
    raise KernelCError("no RISC-V objdump; run `make verify`")


def instruction_census(kernel: Path, prefix: str) -> dict[str, int]:
    dump = subprocess.run(
        [f"{prefix}objdump", "-d", "--no-show-raw-insn", str(kernel)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    lines = [line for line in dump.splitlines() if INSTRUCTION.match(line)]
    return {
        "instructions": len(lines),
        "floating_point": sum(1 for line in lines if FP_OPERAND.search(line)),
    }


def defined_symbols(kernel: Path, prefix: str) -> set[str]:
    listing = subprocess.run(
        [f"{prefix}nm", "--defined-only", str(kernel)], capture_output=True, text=True, check=True
    ).stdout
    return {line.split()[-1] for line in listing.splitlines() if len(line.split()) >= 3}


def reimplemented(kernel_dir: Path) -> dict[str, list[str]]:
    out = {}
    for name in LIBRARY_SOURCES:
        source = kernel_dir / name
        if not source.exists():
            continue
        out[name] = sorted(set(DEFINITION.findall(source.read_text())))
    return out


def pool_bounds(kernel_dir: Path) -> dict[str, int]:
    """The compile-time bounds that stand in for an allocator.

    param.h defines some of them in terms of others — NBUF is MAXOPBLOCKS * 3 — so every macro in
    the header is read first and then resolved to a number, repeatedly, until nothing more can be
    worked out. Reading only the names the chapter quotes gave NBUF a size of zero, which is the kind of
    wrong that looks like a fact.
    """
    text = (kernel_dir / "param.h").read_text()
    defines = dict(
        re.findall(r"^#define\s+([A-Z][A-Z0-9_]*)\s+(.+?)\s*(?://.*)?$", text, re.MULTILINE)
    )

    resolved: dict[str, int] = {}
    for _ in range(len(defines)):
        for name, expression in defines.items():
            if name in resolved:
                continue
            substituted = re.sub(
                r"\b([A-Z][A-Z0-9_]*)\b",
                lambda m: str(resolved.get(m.group(1), m.group(1))),
                expression,
            )
            try:
                resolved[name] = int(eval(substituted, {"__builtins__": {}}, {}))  # noqa: S307
            except Exception:  # noqa: BLE001 — not yet resolvable, or not a number at all
                continue

    bounds = {name: resolved[name] for name in POOL_BOUNDS if name in resolved}
    empty = sorted(name for name, value in bounds.items() if value <= 0)
    if empty:
        raise KernelCError(
            f"{empty} resolved to a bound of zero or less. A pool of no elements is a parsing "
            "failure rather than a fact about the kernel; read kernel/param.h."
        )
    missing = sorted(set(POOL_BOUNDS) - set(bounds))
    if missing:
        raise KernelCError(f"kernel/param.h no longer defines {missing}")
    return bounds


def capture() -> dict[str, Any]:
    stage = xv6.build()
    kernel = stage / "kernel" / "kernel"
    if not kernel.exists():
        raise KernelCError(f"{kernel} is not built; run `python3 scripts/xv6-run.py --build-only`")
    prefix = toolprefix()

    counts = instruction_census(kernel, prefix)
    symbols = defined_symbols(kernel, prefix)
    heap = sorted(name for name in HEAP_FUNCTIONS if name in symbols)
    library = reimplemented(stage / "kernel")
    bounds = pool_bounds(stage / "kernel")

    if counts["floating_point"]:
        raise KernelCError(
            f"{counts['floating_point']} instruction(s) in the kernel name a floating-point "
            "register. The chapter says this kernel has none, and explains a context switch that does "
            "not save them — if that has changed, the chapter is now wrong about something it "
            "uses to make a point about what a kernel chooses not to support."
        )
    if heap:
        raise KernelCError(
            f"the kernel defines {heap}. The chapter's whole second section is that there is no heap "
            "here and that objects come from fixed arrays instead."
        )
    if not any(library.values()):
        raise KernelCError(
            "no reimplemented library functions found. Either the kernel has stopped carrying "
            "its own string routines or the definition-matching has broken; read "
            "kernel/string.c before changing the number."
        )

    return build_result(
        name="kernelc-xv6",
        target="xv6",
        kind="artefact",
        summary={
            "kernel": counts,
            "heap_functions": heap,
            "reimplemented": library,
            "reimplemented_count": sum(len(names) for names in library.values()),
            "pool_bounds": bounds,
        },
        code_sources=["bench/run_kernelc.py"],
        toolchain={
            "cc": "xv6's own CFLAGS",
            "flags": f"{prefix}objdump -d; {prefix}nm --defined-only",
            "execution": "none — the built kernel is read, not run",
        },
        machine={
            "kind": "toolchain",
            "arch": "riscv64",
            "measured_under": "compilation",
            "kernel": f"xv6-riscv @ {xv6_commit()}",
            "model": "the staged kernel, read rather than booted",
        },
        conditions={
            "note": "counts and names only; nothing here was executed",
            "why": "the chapter's claims about what the kernel lacks should fail when it gains them",
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-walk and compare; write nothing")
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
        print(
            f"{payload['name']}: unchanged — the kernel still lacks what the chapter says it lacks"
        )
        return 0
    print(f"{payload['name']}: the kernel has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_kernelc\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
