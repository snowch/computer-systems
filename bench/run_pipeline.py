#!/usr/bin/env python3
"""Chapter 17's artefact: what the core is given to work with.

    python3 -m bench.run_pipeline           # classify the instructions in each variant
    python3 -m bench.run_pipeline --check   # re-classify and compare; write nothing

Two things this can establish without a machine, and they are the two the chapter opens with.

**Whether there is a branch to mispredict at all.** A loop written with an `if` may contain no
branch: a compiler that can see both sides are cheap replaces it with a conditional increment, and
a chapter measuring branch prediction on that loop is measuring nothing. The classification below
is how the book found that out about its own code rather than discovering it in the numbers.

**How much parallelism the source offers.** The four sums do the same additions with different
numbers of accumulators, so they differ in the length of the dependent chain and not in the work.
Instruction counts see that exactly backwards — the shortest program has the longest chain — which
is [ch16]'s closing point made concrete.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_toolchain,
    load_result,
    measurement_differences,
    write_result,
)

ARCH = "aarch64"
SOURCE = "bench/results/pipeline-aarch64.json"

#: AArch64's conditional-select family: the instructions a compiler uses when it decides a branch
#: is not worth the risk of being wrong about.
IF_CONVERTED = ("csel", "csinc", "cinc", "cset", "csinv", "cneg", "csneg")


def classify(text: str) -> dict[str, int]:
    body = [line.split(":\t", 1)[1] for line in text.splitlines() if ":\t" in line]
    mnemonics = [line.split()[0] for line in body if line.strip()]
    return {
        "instructions": len(mnemonics),
        "conditional_branches": sum(1 for m in mnemonics if m.startswith("b.")),
        "calls": sum(1 for m in mnemonics if m == "bl"),
        "if_converted": sum(1 for m in mnemonics if m in IF_CONVERTED),
    }


def capture() -> dict[str, Any]:
    listings = load_result("pipeline-aarch64")["summary"]["listings"]
    shapes = {name: classify(entry["text"]) for name, entry in listings.items()}

    branchy = shapes["sysfs_count_over_calling"]
    flattened = shapes["sysfs_count_over"]
    if flattened["if_converted"] == 0:
        raise RuntimeError(
            "sysfs_count_over still contains a branch, so this compiler did not if-convert it and "
            "ch17's opening finding no longer holds. The chapter says the compiler removed the "
            "branch; check whether that is still true before re-stamping."
        )
    if branchy["conditional_branches"] <= flattened["conditional_branches"]:
        raise RuntimeError(
            "the variant with a call in it has no more branches than the one without, so the "
            "chapter has no branch to measure after all"
        )

    return build_result(
        name="pipeline-shapes",
        target="host",
        kind="artefact",
        summary={"shapes": shapes},
        code_sources=["bench/run_pipeline.py", "sysfs/lib/pipeline.c", SOURCE],
        toolchain={
            "cc": compiler_version(f"{ARCH}-linux-gnu-gcc"),
            "flags": "as recorded in pipeline-aarch64.json",
            "execution": "none — a classification of instructions already captured",
        },
        machine=describe_toolchain(ARCH),
        conditions={"note": "what the core is given; what it does with it needs the board"},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-classify and compare")
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
        print(f"{payload['name']}: unchanged — the core is still given the same to work with")
        return 0
    print(f"{payload['name']}: the shapes have MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_pipeline\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
