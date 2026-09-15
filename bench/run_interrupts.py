#!/usr/bin/env python3
"""Chapter 9's measurement: how much interrupting a fixed amount of I/O takes.

    python3 -m bench.run_interrupts           # boot, run the workload, read the census
    python3 -m bench.run_interrupts --check   # re-run and compare; write nothing

The chapter's finding is in what this refuses to record.

`intrload` writes a fixed number of characters and does a fixed number of block operations. The
**disk** interrupt count is the same on every run, because a block request is a discrete thing a
device completes exactly once. The **console** interrupt count is not: five runs of the identical
workload produced five different numbers, because an interrupt from a character device is a
notification that it is ready for more, and how many of those you need depends on how the timing
fell out rather than on how many characters there were.

So one of them is a property of the workload and the other is a property of the afternoon, and
this runner records the first and declines the second — for the same reason ch08 declines to
record timer interrupts, which is also why the timer is missing here.

What it does record about the console is the fact that survives: how many characters the writing
process handed to the device itself, and how many times it had to stop and wait. The second of
those is zero, every time, and that zero is the chapter.
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

WORKLOAD = ["intrload"]
PATCH = "xv6/patches/11-interrupt-census.patch"
APP = "xv6/apps/intrload.c"

#: Ctrl-N, which the patch binds to printing the census.
DUMP = "\x0e"


def _image_digest() -> str:
    """A digest of the filesystem image the run booted from."""
    image = xv6.STAGE / "fs.img"
    return hashlib.sha256(image.read_bytes()).hexdigest()[:16] if image.exists() else "absent"


class IntrCensusError(RuntimeError):
    """The kernel did not print an interrupt census, or printed one that cannot be believed."""


def read_census(transcript: str) -> dict[str, Any]:
    source: dict[str, int] = {}
    console: dict[str, int] = {}
    declared: dict[str, int] = {}
    complete = False

    for raw in transcript.splitlines():
        if "end intrcensus" in raw:
            complete = True
            continue
        marker = raw.find("intrload chars ")
        if marker >= 0:
            parts = raw[marker:].split()
            declared = {"chars": int(parts[2]), "blocks": int(parts[4])}
            continue
        marker = raw.find("intrcensus ")
        if marker < 0:
            continue
        parts = raw[marker:].split()
        match parts[1:]:
            case ["source", "timer", timer, "uart", uart, "virtio", virtio, "unexpected", other]:
                source = {
                    "timer": int(timer),
                    "uart": int(uart),
                    "virtio": int(virtio),
                    "unexpected": int(other),
                }
            case ["console", "written", written, "sleeps", sleeps, "wakeups", wake, "received", rx]:
                console = {
                    "chars_written": int(written),
                    "write_sleeps": int(sleeps),
                    "tx_wakeups": int(wake),
                    "rx_chars": int(rx),
                }

    if not complete or not source or not console or not declared:
        raise IntrCensusError(
            f"no usable interrupt census in the transcript:\n{transcript[-2000:]}"
        )
    return {"source": source, "console": console, "declared": declared}


def believe(census: dict[str, Any]) -> dict[str, Any]:
    """Keep what the workload decided; drop what the clock decided, and say which is which."""
    source, console, declared = census["source"], census["console"], census["declared"]

    if source["unexpected"]:
        raise IntrCensusError(
            f"{source['unexpected']} interrupt(s) arrived from a device this machine is not "
            "supposed to have, so the census is describing something other than the workload"
        )
    if console["chars_written"] < declared["chars"]:
        raise IntrCensusError(
            f"the workload wrote {declared['chars']} characters and the driver counted "
            f"{console['chars_written']}. Either the program or the patch has changed."
        )

    return {
        # Decided by the workload: a block request is completed once, and it is completed by a
        # device that says so exactly once.
        "block_operations": declared["blocks"] * 2,  # written once, read back once
        "disk_interrupts": source["virtio"],
        # Decided by the workload: every character it asked for reached the device.
        "chars_requested": declared["chars"],
        "chars_the_writer_moved_itself": console["chars_written"],
        "times_the_writer_had_to_wait": console["write_sleeps"],
        "chars_received": console["rx_chars"],
        # Deliberately absent: `timer` and `uart`. See the module docstring.
        "counts_not_recorded": ["timer", "uart"],
    }


def capture() -> dict[str, Any]:
    xv6.require()
    result = xv6.boot([*WORKLOAD, DUMP])
    if result.timed_out:
        raise IntrCensusError(f"xv6 did not finish the workload:\n{result.transcript[-2000:]}")
    return build_result(
        name="interrupts-xv6",
        target="xv6",
        summary={"intrload": believe(read_census(result.transcript)), "workload": WORKLOAD},
        code_sources=["bench/run_interrupts.py", "bench/xv6.py", APP, PATCH],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "qemu-system-riscv64 -machine virt",
        },
        machine=describe_qemu(),
        conditions={
            "cpus": xv6.DEFAULT_CPUS,
            "note": "counts only; nothing here was timed, and two counts are deliberately absent",
            "omitted": "timer and UART interrupt counts, which measure elapsed time rather than work",
            "disk": "the image is opened with snapshot=on, so every run starts from the same filesystem",
            # The disk figure depends on the filesystem image, and the image depends on which
            # programs the book has added to xv6 — so a later chapter adding one moves this
            # number for a reason that has nothing to do with interrupts. Nothing else in the
            # stamping scheme covers fs.img, because nothing else has needed to; recording its
            # digest here makes the dependency visible in the result rather than surprising
            # somebody in six chapters' time. `--check` is what actually catches a change.
            "filesystem_image": _image_digest(),
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
        print(f"{payload['name']}: unchanged — the same I/O still takes the same interrupting")
        return 0
    print(f"{payload['name']}: the interrupt census has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_interrupts\n"
        "  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
