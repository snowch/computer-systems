#!/usr/bin/env python3
"""Chapter 8's measurement: what choosing an allocation policy costs.

    python3 -m bench.run_faults           # boot, run the workload, read the fault census
    python3 -m bench.run_faults --check   # re-run and compare; write nothing

This kernel already offers both policies — ``sbrk`` allocates when you ask, ``sbrklazy`` allocates
when you touch — so the book has no policy to implement and no business implementing one. The
patch counts and changes nothing. What is missing from the kernel, and from most accounts of
laziness, is the exchange rate: how many pages are saved, and how many entries into the kernel are
bought with them.

Deterministic by construction rather than by observation, which is the ch06 lesson applied before
rather than after. ``faultload`` decides how much it asks for and how much of it it touches, and
prints both; the kernel counts independently; this runner refuses to stamp a result in which the
two disagree. The shell allocates as well, which is why the census is per process and why only
``faultload``'s row is recorded.
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
    compiler_version,
    describe_qemu,
    load_result,
    measurement_differences,
    write_result,
)

WORKLOAD = ["faultload"]
PATCH = "xv6/patches/08-fault-census.patch"
APP = "xv6/apps/faultload.c"

#: Ctrl-F, which the patch binds to printing the census.
DUMP = "\x06"


class FaultCensusError(RuntimeError):
    """The kernel did not print a fault census, or printed one that cannot be believed."""


def read_census(transcript: str) -> dict[str, Any]:
    """The workload's own account of what it did, and the kernel's account of the same run."""
    declared: dict[str, int] = {}
    counted: dict[str, int] = {}
    complete = False

    for raw in transcript.splitlines():
        if "end faultcensus" in raw:
            complete = True
            continue
        marker = raw.find("faultload asked_lazy")
        if marker >= 0:
            parts = raw[marker:].split()
            declared = {
                "asked_lazy": int(parts[2]),
                "touched_lazy": int(parts[4]),
                "asked_eager": int(parts[6]),
            }
            continue
        marker = raw.find("faultcensus exited ")
        if marker < 0:
            continue
        parts = raw[marker:].split()
        match parts[1:]:
            case [
                "exited", name,
                "eager", eager, "lazy", lazy,
                "load", load, "store", store,
                "refused", refused,
            ]:  # fmt: skip
                counted = {
                    "name": name,
                    "eager_pages": int(eager),
                    "lazy_pages": int(lazy),
                    "load_faults": int(load),
                    "store_faults": int(store),
                    "refused": int(refused),
                }

    if not complete or not counted or not declared:
        raise FaultCensusError(f"no usable fault census in the transcript:\n{transcript[-2000:]}")
    return {"declared": declared, "counted": counted}


def believe(census: dict[str, Any]) -> dict[str, Any]:
    """Refuse anything the workload and the kernel do not both agree on.

    Three separate ways this could be measuring something other than what it claims, and each is
    a refusal rather than a footnote: the census could have latched a different process, the
    kernel could have allocated lazily a different number of times from the number of pages the
    program touched, and a fault the handler declined would mean the program went somewhere it
    had not asked for.
    """
    declared, counted = census["declared"], census["counted"]
    if counted["name"] != WORKLOAD[0]:
        raise FaultCensusError(
            f"the census latched {counted['name']!r} rather than {WORKLOAD[0]!r}, so these counts "
            "belong to a different program"
        )
    if counted["lazy_pages"] != declared["touched_lazy"]:
        raise FaultCensusError(
            f"{WORKLOAD[0]} touched {declared['touched_lazy']} lazily-requested pages and the "
            f"kernel allocated {counted['lazy_pages']}. Either the program or the patch changed."
        )
    faults = counted["load_faults"] + counted["store_faults"]
    if faults != declared["touched_lazy"]:
        raise FaultCensusError(
            f"{declared['touched_lazy']} first touches should be {declared['touched_lazy']} "
            f"faults; the kernel counted {faults}."
        )
    if counted["refused"]:
        raise FaultCensusError(
            f"the handler refused {counted['refused']} fault(s), which means the workload went "
            "outside the memory it asked for. That is a bug in the workload, not a measurement."
        )

    # What exec spent before main ran. Not a residual to be embarrassed about: it is the price of
    # starting a process at all, and it is the baseline every other number here sits on top of.
    return {
        **counted,
        **declared,
        "pages_never_allocated": declared["asked_lazy"] - declared["touched_lazy"],
        "eager_pages_before_main": counted["eager_pages"] - declared["asked_eager"],
    }


def capture() -> dict[str, Any]:
    xv6.require()
    result = xv6.boot([*WORKLOAD, DUMP])
    if result.timed_out:
        raise FaultCensusError(f"xv6 did not finish the workload:\n{result.transcript[-2000:]}")
    summary = {"faultload": believe(read_census(result.transcript)), "workload": WORKLOAD}
    return build_result(
        name="faults-xv6",
        target="xv6",
        summary=summary,
        code_sources=["bench/run_faults.py", "bench/xv6.py", APP, PATCH],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "qemu-system-riscv64 -machine virt",
        },
        machine=describe_qemu(),
        conditions={
            "cpus": xv6.DEFAULT_CPUS,
            "note": "counts only: pages allocated and faults taken; nothing here was timed",
            "policies": "both are this kernel's own — sbrk allocates on request, sbrklazy on touch",
            "attribution": "per process, and only the workload's row is recorded; the shell allocates too",
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
        print(f"{payload['name']}: unchanged — the same workload still costs the same")
        return 0
    print(f"{payload['name']}: the fault census has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_faults\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
