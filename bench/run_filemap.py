#!/usr/bin/env python3
"""Appendix D's artefact: the kernel's files, measured from the tree the reader actually has.

    python3 -m bench.run_filemap           # walk the submodule and stamp what is there
    python3 -m bench.run_filemap --check   # re-walk and diff; write nothing

A file map written by hand describes the version of xv6 its author was reading. This one is
walked from the submodule at its pinned commit, so a line count in the appendix is a line count a
reader can reproduce with `wc -l`, and a file that appears or disappears upstream fails CI rather
than quietly making the appendix wrong.

Which chapter reads which file is the one editorial judgement here, and it lives in ``READS``
below so that it is reviewable in one place. It is checked against the tree: a mapping naming a
file the submodule does not have refuses to stamp, which is how this would fail after an upstream
rename.
"""

from __future__ import annotations

import argparse
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

KERNEL = "kernel"

#: Which chapter of this book reads which file of the kernel, and what it goes there for.
#:
#: Only files a chapter genuinely reads. A map of everything would be a directory listing, which
#: the reader already has; the useful thing is knowing which of forty files matters for the
#: chapter open in front of them.
READS: dict[str, tuple[str, str]] = {
    "entry.S": ("ch06", "the first instructions the kernel runs, before there is a stack"),
    "start.c": ("ch06", "the machine-mode setup that hands over to supervisor mode"),
    "trampoline.S": ("ch06", "uservec and userret — the register moves ch06 counts"),
    "trap.c": ("ch06", "where a trap is decided, and where a page fault would be handled"),
    "syscall.c": ("ch06", "the dispatch table, and how arguments cross the boundary"),
    "syscall.h": ("ch06", "the call numbers"),
    "sysproc.c": ("ch06", "the process calls, including the one ch06's workload uses"),
    "vm.c": ("ch07", "the page-table walk, mapping, and the kernel's own address space"),
    "riscv.h": ("ch07", "the Sv39 field definitions, as macros over a 64-bit word"),
    "memlayout.h": ("ch07", "what is mapped where, and why the trampoline is at the top"),
    "kalloc.c": ("ch08", "the physical page allocator a fault ends up calling"),
    "exec.c": ("ch08", "what a fresh address space is built out of"),
    "kernelvec.S": ("ch09", "the trap path taken when the kernel itself is interrupted"),
    "plic.c": ("ch09", "which device is allowed to interrupt which hart"),
    "console.c": ("ch09", "a device driver small enough to read in full"),
    "uart.c": ("ch09", "the registers underneath it"),
    "spinlock.c": ("ch10", "the lock, and the memory barriers around it"),
    "spinlock.h": ("ch10", "what a lock is made of"),
    "sleeplock.c": ("ch10", "the other kind, and when each is correct"),
    "proc.c": ("ch11", "the scheduler, and both halves of a context switch"),
    "proc.h": ("ch11", "the context ch11 counts the registers of"),
    "swtch.S": ("ch11", "the switch itself — fourteen registers and nothing else"),
    "bio.c": ("ch12", "the buffer cache, and why a read can cost nothing"),
    "log.c": ("ch12", "the write-ahead log ch12 counts the amplification of"),
    "fs.c": ("ch12", "inodes, blocks, and the path from a name to a byte"),
    "file.c": ("ch12", "what a file descriptor actually is"),
    "virtio_disk.c": ("ch12", "the only device in the system that makes you wait"),
}


class FileMapError(RuntimeError):
    """The map stopped describing the tree."""


def walk(kernel_dir: Path) -> dict[str, Any]:
    files = {}
    for path in sorted(kernel_dir.iterdir()):
        if path.suffix not in (".c", ".h", ".S"):
            continue
        text = path.read_text(errors="replace")
        files[path.name] = {
            "lines": len(text.splitlines()),
            "bytes": len(text.encode()),
        }
    return files


def capture() -> dict[str, Any]:
    kernel_dir = xv6.XV6_SUBMODULE / KERNEL
    if not kernel_dir.is_dir():
        raise FileMapError(
            f"{kernel_dir} is not there. Run `git submodule update --init --recursive`."
        )
    files = walk(kernel_dir)

    missing = sorted(name for name in READS if name not in files)
    if missing:
        raise FileMapError(
            f"READS names {missing}, which the submodule does not have. Upstream has renamed or "
            "removed them; fix the map rather than the check, and read appendix D afterwards to "
            "see what else it now says wrongly."
        )

    return build_result(
        name="filemap-xv6",
        target="xv6",
        kind="artefact",
        summary={
            "files": files,
            "reads": {name: {"chapter": ch, "for": why} for name, (ch, why) in READS.items()},
            "total_lines": sum(entry["lines"] for entry in files.values()),
            "mapped_lines": sum(files[name]["lines"] for name in READS),
        },
        code_sources=["bench/run_filemap.py"],
        toolchain={
            "cc": "none",
            "flags": "none",
            "execution": "none — the tree is read, not built",
        },
        machine={
            # Not describe_qemu(): nothing here was emulated, or built, or run. What this result
            # describes is a source tree, and the only provenance that matters is which commit of
            # it — which is what a reader would have to check out to see these line counts.
            "kind": "toolchain",
            "arch": "riscv64",
            "measured_under": "compilation",
            "kernel": f"xv6-riscv @ {xv6_commit()}",
            "model": "the xv6 submodule's source, read rather than built",
        },
        conditions={
            "note": "line counts of the submodule at its pinned commit; nothing was compiled",
            "why": "a hand-written file map describes whichever xv6 its author was reading",
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
        print(f"{payload['name']}: unchanged — the kernel is still the tree appendix D describes")
        return 0
    print(f"{payload['name']}: the kernel tree has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_filemap\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
