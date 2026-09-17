#!/usr/bin/env python3
"""The memory-as-one-array chapter's first artefact: what one complete C program prints.

    python3 -m bench.run_firstc           # run it and stamp what it said
    python3 -m bench.run_firstc --check    # re-run and compare; write nothing

Small, and it earns its place twice. It is the first thing in the book a reader who has never
written C can compile and run, so the chapter needs its output to be quotable rather than
asserted. And it is the same fact the chapter's disassembly then shows from underneath — that `p + 1`
moves by the size of an element — arrived at first by watching a program say so.

**No address is recorded, deliberately.** One would differ on every run and would be a number the
book could not commit to. What is stable, and what the chapter is actually about, is the
relationships between addresses: that `&` and `*` undo each other, and that the distance from one
element to the next is the element's size.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.measure import compile_program, resolve_host_target
from bench.stamp import (
    ROOT,
    build_result,
    describe_counted_run,
    load_result,
    measurement_differences,
    write_result,
)

PROGRAM = "sysfs/tools/firstc.c"


class FirstCError(RuntimeError):
    """The program stopped saying what the chapter quotes it as saying."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {"steps": {}}
    complete = False
    for line in text.splitlines():
        match line.split():
            case ["firstc", "value", value, "roundtrip", roundtrip]:
                facts |= {"value": int(value), "roundtrip": int(roundtrip)}
            case ["firstc", "step", kind, distance]:
                facts["steps"][kind] = int(distance)
            case ["end", "firstc"]:
                complete = True
    if not complete:
        raise FirstCError(f"firstc did not finish:\n{text[-2000:]}")
    return facts


def capture() -> dict[str, Any]:
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    target = resolve_host_target()
    built = compile_program([PROGRAM], build_dir / "firstc", target, includes=["sysfs/include"])
    facts = parse(built.run().stdout)

    if facts["value"] != facts["roundtrip"]:
        raise FirstCError(
            f"`*&value` gave {facts['roundtrip']} where `value` is {facts['value']}. The chapter's first "
            "claim is that the two are inverses; if they are not, the chapter is wrong about the "
            "only thing it asks the reader to take on trust."
        )
    if facts["steps"].get("int64") != 2 * facts["steps"].get("int32", 0):
        raise FirstCError(
            f"the two element steps are {facts['steps']}, and the chapter's point is that one is twice "
            "the other because the element is twice as wide. On a machine where that does not "
            "hold the chapter needs rewriting, not re-running."
        )

    return build_result(
        name="firstc",
        target="host",
        kind="artefact",
        summary=facts | {"built_for": target.name},
        code_sources=["bench/run_firstc.py", PROGRAM],
        toolchain={
            "cc": target.cc,
            "flags": " ".join(target.flags),
            "execution": "run for what it prints; no duration is taken or recorded",
        },
        machine=describe_counted_run("aarch64"),
        conditions={
            "note": "relationships between addresses, never an address",
            "why": "an address differs on every run; the distance between two does not",
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
        print(
            f"{payload['name']}: unchanged — the first program still says what the chapter quotes"
        )
        return 0
    print(f"{payload['name']}: has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
