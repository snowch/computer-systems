#!/usr/bin/env python3
"""Chapter 5's artefact: what is actually in an xv6 binary.

    python3 -m bench.run_elf           # read the binaries and stamp what is in them
    python3 -m bench.run_elf --check   # re-read and compare; write nothing

Structure, not cost. Sections, segments and symbol counts are facts about a file, read by the
book's own reader rather than by ``readelf`` — which is the point of ch05 having written one.

The subject is xv6's own programs, built by xv6's Makefile with xv6's linker script, because a
Linux binary's answer to "where does this get loaded" is complicated by a dynamic loader and a
position-independent layout that would take a chapter of their own to explain. xv6 links a
program to a fixed address and puts it there, which is the mechanism underneath the complicated
version.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from bench import xv6
from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

READER = "sysfs/tools/elfdump.c"

#: The programs looked at. One of the book's own and one of xv6's, so the numbers are not an
#: artefact of how this book happens to write C.
SUBJECTS = ("_sameanswer", "_ls")


class ElfError(RuntimeError):
    """The reader did not say what the reader says."""


def parse(text: str) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}
    complete = False
    for raw in text.splitlines():
        parts = raw.split()
        match parts:
            case ["section", name, addr, size, flags]:
                sections.append(
                    {"name": name, "addr": int(addr), "size": int(size), "flags": int(flags)}
                )
            case ["segment", vaddr, filesz, memsz, flags, align]:
                segments.append(
                    {
                        "vaddr": int(vaddr),
                        "file_bytes": int(filesz),
                        "memory_bytes": int(memsz),
                        "flags": int(flags),
                        "align": int(align),
                    }
                )
            case ["symbols", defined, undefined]:
                facts["defined_symbols"] = int(defined)
                facts["undefined_symbols"] = int(undefined)
            case ["entry", value]:
                facts["entry"] = int(value)
            case ["end", "elfdump"]:
                complete = True
    if not complete:
        raise ElfError(f"the reader was cut off; got:\n{text}")
    return {"sections": sections, "segments": segments, **facts}


def read_with_our_own_reader(build_dir: Path) -> dict[str, Any]:
    """Build elfdump for this machine and point it at xv6's binaries."""
    xv6.require()
    xv6.build()
    native = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)
    built = compile_program([READER], build_dir / "elfdump", native)

    programs: dict[str, Any] = {}
    for name in SUBJECTS:
        binary = xv6.STAGE / "user" / name
        if not binary.exists():
            raise ElfError(f"{binary} was not built")
        printed = subprocess.run(
            [str(built.path), str(binary)], capture_output=True, text=True, check=True
        ).stdout
        programs[name.lstrip("_")] = parse(printed)
    return programs


def capture() -> dict[str, Any]:
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    programs = read_with_our_own_reader(build_dir)
    return build_result(
        name="elf-xv6",
        target="xv6",
        kind="artefact",
        summary={"programs": programs},
        code_sources=["bench/run_elf.py", READER],
        toolchain={
            "cc": compiler_version("cc"),
            "flags": "the reader is built for this machine; the subjects are built by xv6",
            "execution": "none — files were read, not run",
        },
        machine=describe_toolchain("riscv64"),
        conditions={
            "note": "structure only: sections, segments and symbol counts",
            "subjects": "xv6 user programs, linked by xv6's own Makefile and linker script",
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
        print(f"{payload['name']}: unchanged — these binaries still have this shape")
        return 0
    print(f"{payload['name']}: the binaries have CHANGED\n")
    for difference in differences:
        print(f"  {difference}")
    print("\nRe-run and commit:\n  python3 -m bench.run_elf\n  python3 scripts/render-figures.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
