#!/usr/bin/env python3
"""Chapter 13's artefact: the same program on both targets, and what they agree about.

    python3 -m bench.run_bridge           # run it on both targets and stamp what they said
    python3 -m bench.run_bridge --check   # re-run and compare; write nothing

One source, two routes through the same data, two targets. What is recorded here is everything the
two targets agree about — the answer, the structure, the instruction counts — and the point of the
chapter is that the list is complete and predicts nothing about cost.

The duration is not here and cannot be. It is `ch13-cost`, which is declared pending until
``make bench-board`` runs on the reference machine, and the chapter is written so that the
argument stands either way: what Parts I and II establish about these two functions is the same
whether or not the board has reported.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench import xv6
from bench.measure import compile_program, resolve_host_target
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_counted_run,
    load_result,
    measurement_differences,
    write_result,
)

HOST_PROGRAM = "sysfs/tools/bridgerun.c"
LIBRARY = "sysfs/lib/bridge.c"
XV6_APP = "xv6/apps/bridgerun.c"
HEADER = "sysfs/include/sysfs/bridge.h"

#: The two routes, and the instruction counts that make the chapter's point.
SYMBOLS = ("sysfs_bridge_sequential", "sysfs_bridge_chased")


class BridgeError(RuntimeError):
    """The two targets did not say the same thing, which is the one thing they must."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    complete = False
    for raw in text.splitlines():
        parts = raw.split()
        match parts:
            case ["bridge", "cells", cells, "stride", stride]:
                facts["cells"] = int(cells)
                facts["stride"] = int(stride)
            case ["bridge", "sequential", sequential, "chased", chased, "agree", agree]:
                facts["sequential"] = int(sequential)
                facts["chased"] = int(chased)
                facts["agree"] = agree == "yes"
            case ["end", "bridge"]:
                complete = True
    if not complete or "agree" not in facts:
        raise BridgeError(f"the bridge program was cut off; got:\n{text}")
    return facts


def on_xv6() -> dict[str, Any]:
    xv6.require()
    result = xv6.boot(["bridgerun"])
    if result.timed_out:
        raise BridgeError(f"xv6 did not finish bridgerun:\n{result.transcript[-2000:]}")
    return parse(result.output_of("bridgerun"))


def on_host(build_dir: Path) -> dict[str, Any]:
    """Built for the reference architecture and run for its *answers* — never for a duration."""
    target = resolve_host_target()
    built = compile_program(
        [HOST_PROGRAM], build_dir / "bridgerun", target, includes=["sysfs/include"]
    )
    return {**parse(built.run().stdout), "built_for": target.name}


def instruction_counts() -> dict[str, Any]:
    """What each route costs in instructions, from the listings the chapters print."""
    out: dict[str, Any] = {}
    for arch in ("riscv64", "aarch64"):
        listings = load_result(f"bridge-{arch}")["summary"]["listings"]
        out[arch] = {symbol: listings[symbol]["instructions"] for symbol in SYMBOLS}
    return out


def capture() -> dict[str, Any]:
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    xv6_side = on_xv6()
    host_side = on_host(build_dir)

    for side, facts in (("xv6", xv6_side), ("host", host_side)):
        if not facts["agree"]:
            raise BridgeError(f"the two routes disagreed on the {side} target: {facts}")
    shared = ("cells", "stride", "sequential", "chased")
    differing = {
        key: (xv6_side[key], host_side[key]) for key in shared if xv6_side[key] != host_side[key]
    }
    if differing:
        raise BridgeError(
            "the two targets computed different things, which would make this chapter's whole "
            f"argument false rather than interesting: {differing}"
        )

    return build_result(
        name="bridge-both",
        target="xv6",
        kind="artefact",
        summary={
            "agreed": {key: xv6_side[key] for key in shared},
            "instructions": instruction_counts(),
            "host_built_for": host_side["built_for"],
        },
        code_sources=["bench/run_bridge.py", LIBRARY, HOST_PROGRAM, XV6_APP, HEADER],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS on one side; the book's portable flags on the other",
            "execution": "qemu-system-riscv64 for xv6; user-mode QEMU for the host target's answers",
        },
        machine=describe_counted_run("riscv64"),
        conditions={
            "note": "answers and instruction counts only; no duration appears here by design",
            "why": "a host-target timing is only taken on the board, by make bench-board",
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
        print(f"{payload['name']}: unchanged — both targets still agree about all of this")
        return 0
    print(f"{payload['name']}: the two targets have MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_bridge\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
