#!/usr/bin/env python3
"""Chapter 12's measurement: what one byte costs the disk.

    python3 -m bench.run_blocks           # boot, run both workloads, read the censuses
    python3 -m bench.run_blocks --check   # re-run and compare; write nothing

An amplification factor, measured as a difference so that it means what it says. Running any
program costs the file system something before `main` starts, and charging that to the byte would
inflate the answer by more than the answer. So `blockload` performs the same operations twice,
differing in one `write` call, the census is zeroed before each, and what is subtracted is
everything that is not the byte.

Deterministic for the same filesystem image, which [ch11] established and which this runner
depends on more heavily: block counts are decided by where the file system puts things.
"""

from __future__ import annotations

import argparse
import hashlib
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

PATCH = "xv6/patches/14-block-census.patch"
APP = "xv6/apps/blockload.c"

RESET = "\x1a"  # Ctrl-Z, which the patch binds to zeroing the census
DUMP = "\x02"  # Ctrl-B, which prints it

#: The shell runs the quiet workload once before anything is measured, so that the binary and the
#: directory are already in the buffer cache and the two measured runs start from the same place.
COMMANDS = [
    "blockload quiet",
    RESET,
    "blockload quiet",
    DUMP,
    RESET,
    "blockload byte",
    DUMP,
]

BLOCK_BYTES = 512


class BlockCensusError(RuntimeError):
    """The kernel did not print two block censuses, or printed ones that cannot be believed."""


def read_censuses(transcript: str) -> list[dict[str, int]]:
    out: list[dict[str, int]] = []
    for raw in transcript.splitlines():
        marker = raw.find("blockcensus reads ")
        if marker < 0:
            continue
        parts = raw[marker:].split()
        out.append(
            {
                "reads": int(parts[2]),
                "writes": int(parts[4]),
                "logged": int(parts[6]),
                "commits": int(parts[8]),
            }
        )
    if len(out) != 2:
        raise BlockCensusError(f"expected two censuses and found {len(out)}:\n{transcript[-2000:]}")
    return out


def believe(censuses: list[dict[str, int]]) -> dict[str, Any]:
    quiet, byte = censuses
    marginal = {key: byte[key] - quiet[key] for key in quiet}

    if marginal["writes"] <= 0:
        raise BlockCensusError(
            "writing a byte cost no more block writes than not writing it, which cannot be right "
            "and means the two runs are not differing in what this thinks they are"
        )
    expected = 2 * marginal["logged"] + 2 * marginal["commits"]
    if expected != marginal["writes"]:
        # Not a law of file systems; a law of *this* one, and worth failing on rather than
        # explaining away. A committed transaction writes each of its blocks to the log and then
        # to its home, and writes the log header twice around them — so the writes a byte causes
        # should be twice the blocks it logged plus twice the transactions it committed.
        #
        # The first version of this check said simply twice the blocks, and passed, because the
        # counter was counting `log_write` calls rather than blocks and xv6 absorbs a repeated
        # write to the same block. Two wrong numbers agreeing is the failure mode a cross-check
        # exists to catch, and it only caught it once the counter was moved past the absorption.
        raise BlockCensusError(
            f"{marginal['logged']} blocks logged in {marginal['commits']} transaction(s) should "
            f"cost {expected} writes and cost {marginal['writes']}; the chapter's explanation of "
            "its own number no longer holds."
        )

    return {
        "creating_an_empty_file": quiet,
        "and_writing_one_byte": byte,
        "the_byte_alone": marginal,
        "bytes_written_for_one_byte": marginal["writes"] * BLOCK_BYTES,
        "bytes_written_for_no_bytes": quiet["writes"] * BLOCK_BYTES,
    }


def capture() -> dict[str, Any]:
    xv6.require()
    result = xv6.boot(COMMANDS)
    if result.timed_out:
        raise BlockCensusError(f"xv6 did not finish the workload:\n{result.transcript[-2000:]}")
    image = xv6.STAGE / "fs.img"
    return build_result(
        name="blocks-xv6",
        target="xv6",
        summary={"blockload": believe(read_censuses(result.transcript))},
        code_sources=["bench/run_blocks.py", "bench/xv6.py", APP, PATCH],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "qemu-system-riscv64 -machine virt",
        },
        machine=describe_qemu(),
        conditions={
            "cpus": xv6.DEFAULT_CPUS,
            "note": "block counts only; nothing here was timed",
            "method": "a difference between two runs of the same program, one of which writes a byte",
            "filesystem_image": hashlib.sha256(image.read_bytes()).hexdigest()[:16],
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
        print(f"{payload['name']}: unchanged — one byte still costs the disk this much")
        return 0
    print(f"{payload['name']}: the block census has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_blocks\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
