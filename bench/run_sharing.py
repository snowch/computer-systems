#!/usr/bin/env python3
"""Chapter 18's artefact: which counters share a cache line.

    python3 -m bench.run_sharing           # read the layouts and stamp them
    python3 -m bench.run_sharing --check   # re-read and compare; write nothing

The question that decides whether two cores will fight — do these two fields land on the same
line — is answered by the compiler and the layout, so it can be answered here. What the fight
costs needs four cores and is `ch25-sharing`, pending on the board.

Built for the reference architecture and run under user-mode QEMU for its *answers*, which is the
same arrangement [ch20] uses: a layout is a fact about a data model and an ABI, and both are
present in a cross build.
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
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

TOOL = "sysfs/tools/layout.c"
LIBRARY = "sysfs/lib/sharing.c"
HEADER = "sysfs/include/sysfs/sharing.h"


class LayoutError(RuntimeError):
    """The layouts are not what this chapter is about."""


def parse(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    complete = False
    for raw in text.splitlines():
        parts = raw.split()
        match parts:
            case ["line", "bytes", value]:
                out["line_bytes"] = int(value)
            case [name, "size", size, "offsets", first, second, "same_line", same]:
                out[name] = {
                    "size": int(size),
                    "offsets": [int(first), int(second)],
                    "same_line": same == "1",
                }
            case ["end", "layout"]:
                complete = True
    if not complete or "packed" not in out or "padded" not in out:
        raise LayoutError(f"the layout tool was cut off; got:\n{text}")
    return out


def capture() -> dict[str, Any]:
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    target = resolve_host_target()
    built = compile_program(
        [TOOL, LIBRARY], build_dir / "layout", target, includes=["sysfs/include"]
    )
    layouts = parse(built.run().stdout)

    if not layouts["packed"]["same_line"]:
        raise LayoutError(
            "the packed structure's two counters are not on the same line, so this chapter has no "
            "false sharing to demonstrate. Either the line size changed or the padding did."
        )
    if layouts["padded"]["same_line"]:
        raise LayoutError(
            "the padded structure's counters share a line, so the padding is not doing its job "
            "and the comparison would show nothing"
        )

    return build_result(
        name="sharing-layout",
        target="host",
        kind="artefact",
        summary={"layouts": layouts, "built_for": target.name},
        code_sources=["bench/run_sharing.py", TOOL, LIBRARY, HEADER],
        toolchain={
            "cc": compiler_version(target.cc),
            "flags": "the book's portable flags",
            "execution": "user-mode QEMU, for the answers only — no duration is taken here",
        },
        machine=describe_toolchain("aarch64"),
        conditions={
            "note": "offsets and sizes only; what sharing a line costs needs four real cores",
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
        print(f"{payload['name']}: unchanged — the fields still land where the book says")
        return 0
    print(f"{payload['name']}: the layouts have MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_sharing\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
