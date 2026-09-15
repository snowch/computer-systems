#!/usr/bin/env python3
"""Chapter 1's artefacts: what each stage of the toolchain hands to the next.

    python3 -m bench.run_stages           # walk the toolchain and stamp the result
    python3 -m bench.run_stages --check   # re-walk and compare; write nothing

Not a measurement. Nothing here is executed and nothing is timed — these are sizes and symbol
counts, facts about files a compiler produced, so they are stamped ``kind: artefact`` and CI
regenerates them on every push exactly as it does the disassembly listings.

The walk itself is ``sysfs/tools/stages.sh``, four commands that differ only in where the compiler
driver is told to stop. This module parses what that prints and adds one fact the shell cannot
reach: the size of the *same program* built as an xv6 user program, against its size built
statically for Linux. That comparison is the chapter's closing figure and it is not subtle.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from bench import xv6
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

WALK = ROOT / "sysfs" / "tools" / "stages.sh"
SOURCE = "sysfs/tools/sameanswer.c"
XV6_APP = "xv6/apps/sameanswer.c"
HEADER = "sysfs/include/sysfs/stages.h"

#: The cross compiler Part III is written against. Named rather than resolved, because this result
#: is a statement about the RISC-V toolchain specifically and picking whatever happens to be
#: installed would make the numbers depend on the machine that ran the script.
CC = "riscv64-linux-gnu-gcc"


class WalkError(RuntimeError):
    """The toolchain walk did not print what a toolchain walk prints."""


def parse_walk(text: str) -> dict[str, Any]:
    """Turn the script's key/value lines into a summary, refusing anything truncated."""
    stages: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}
    complete = False

    for raw in text.splitlines():
        parts = raw.strip().split()
        if not parts:
            continue
        match parts:
            case ["stage", label, size, lines]:
                stages.append({"stage": label, "bytes": int(size), "lines": int(lines)})
            case ["undefined_in_object", value]:
                facts["undefined_in_object"] = int(value)
            case ["undefined_in_program", value]:
                facts["undefined_in_program"] = int(value)
            case ["end", "stagewalk"]:
                complete = True

    if not complete:
        raise WalkError(f"the walk was cut off; got:\n{text}")
    if len(stages) != 4:
        raise WalkError(f"expected four stages, got {[s['stage'] for s in stages]}")
    return {"stages": stages, **facts}


def refuse_a_size_that_describes_this_checkout(scratch: Path) -> None:
    """Stage 1's size has to be a fact about the file, not about where the repository lives.

    The preprocessor writes the name of every file it pasted in, spelled as it was given on the
    command line, into the output it hands the compiler. So an absolute include path makes the
    preprocessed file longer on a machine whose checkout is buried deeper — 38273 bytes here and
    38345 on a CI runner, for a tree identical to the byte. The book caught that the only way it
    was ever going to: the committed number and the regenerated one disagreed, and the disagreement
    was three line markers wide.

    ``stages.sh`` names everything relative to the root so that cannot happen. This is the check
    that it has not quietly stopped doing so, and it looks at every file the walk produced rather
    than only the preprocessed one: an object file or a binary that started embedding its build
    directory would move the same way, for the same reason, and would be harder to spot.
    """
    here = str(ROOT).encode()
    for produced in sorted(scratch.iterdir()):
        if here in produced.read_bytes():
            raise WalkError(
                f"{produced.name} contains the path of this checkout ({ROOT}), so its size is "
                "partly a statement about this machine's directory layout and would differ on "
                "another. Refusing to stamp it. See the comment at the top of sysfs/tools/"
                "stages.sh: every path the walk hands the compiler must be relative to the "
                "repository root."
            )


def walk() -> dict[str, Any]:
    """Run the four commands and read back what they left behind."""
    if not shutil.which(CC):
        raise WalkError(f"{CC} is not installed (see ch00)")
    with tempfile.TemporaryDirectory() as scratch:
        printed = subprocess.run(
            ["sh", str(WALK), SOURCE, scratch, CC],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        ).stdout
        refuse_a_size_that_describes_this_checkout(Path(scratch))
    return parse_walk(printed)


def xv6_program_bytes() -> int:
    """How big the same program is when xv6's user library links it instead of glibc.

    The chapter's closing comparison, and the reason it is worth a line of Python: the two
    numbers differ by more than two orders of magnitude, and a reader who has just watched a
    linker turn 4 kB of object into half a megabyte deserves to know that almost none of it was
    their program.
    """
    xv6.require()
    xv6.build()
    binary = xv6.STAGE / "user" / "_sameanswer"
    if not binary.exists():
        raise WalkError(f"{binary} was not built — is xv6/apps/sameanswer.c staged?")
    return binary.stat().st_size


def capture() -> dict[str, Any]:
    summary = walk()
    summary["xv6_program_bytes"] = xv6_program_bytes()
    summary["linux_program_bytes"] = next(
        stage["bytes"] for stage in summary["stages"] if stage["stage"] == "link"
    )
    return build_result(
        name="stagewalk-riscv64",
        target="xv6",
        kind="artefact",
        summary=summary,
        code_sources=["bench/run_stages.py", "sysfs/tools/stages.sh", SOURCE, XV6_APP, HEADER],
        toolchain={
            "cc": compiler_version(CC),
            "flags": "-O2 -Wall -Wextra -march=rv64gc -mabi=lp64d",
            "execution": "none — four compiler stages, and two files measured",
        },
        machine=describe_toolchain("riscv64"),
        conditions={
            "note": "sizes and symbol counts only; nothing here was executed or timed",
            "linux_link": "statically against glibc, so the binary runs under user-mode QEMU",
            "xv6_link": "against xv6's own user library, by xv6's own Makefile",
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
        print(f"{payload['name']}: unchanged — the toolchain still produces these files")
        return 0
    print(f"{payload['name']}: the toolchain's output has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_stages\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
