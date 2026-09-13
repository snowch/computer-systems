#!/usr/bin/env python3
"""Stage, build and boot xv6 — interactively, under gdb, or scripted.

    python3 scripts/xv6-run.py                 # boot it and take over the terminal
    python3 scripts/xv6-run.py --gdb           # halt at reset, waiting for gdb on :26000
    python3 scripts/xv6-run.py -c ls -c sysprobe   # run commands, print the transcript, exit
    python3 scripts/xv6-run.py --build-only    # stage and compile, boot nothing

The staging tree is ``xv6/stage``, built from the pristine submodule plus ``xv6/apps`` and
``xv6/patches`` (see xv6/README.md). Nothing here ever writes to the submodule, so
``git submodule status`` stays a statement about upstream.

Ctrl-A X quits QEMU in the interactive modes; xv6 itself has no way to halt the machine.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench import xv6  # noqa: E402

GDB_PORT = 26000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-c",
        "--command",
        action="append",
        default=[],
        metavar="CMD",
        help="run CMD at the xv6 shell; repeatable. Implies scripted mode.",
    )
    parser.add_argument("--cpus", type=int, default=xv6.DEFAULT_CPUS)
    parser.add_argument(
        "--gdb", action="store_true", help="wait for gdb before the first instruction"
    )
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0, help="scripted mode only")
    args = parser.parse_args()

    problems = xv6.missing_requirements()
    if problems:
        print("Cannot run the xv6 target:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    stage = xv6.build(cpus=args.cpus)
    print(f"staged and built: {stage.relative_to(ROOT)}", file=sys.stderr)
    if args.build_only:
        return 0

    if args.command:
        result = xv6.boot(args.command, cpus=args.cpus, timeout=args.timeout)
        print(result.transcript, end="")
        if result.timed_out:
            print("\nxv6 did not finish in time.", file=sys.stderr)
            return 1
        return 0

    command = xv6.qemu_command(stage, cpus=args.cpus)
    if args.gdb:
        command += ["-S", "-gdb", f"tcp::{GDB_PORT}"]
        print(
            f"QEMU is halted at reset. In another terminal:\n"
            f"  gdb-multiarch {stage / 'kernel' / 'kernel'} "
            f"-ex 'target remote localhost:{GDB_PORT}'\n"
            "See Appendix B for the rest.",
            file=sys.stderr,
        )
    print("Ctrl-A X quits QEMU.\n", file=sys.stderr)
    # exec, not run: this hands the terminal over, so Ctrl-A and job control behave the way a
    # person at a console expects rather than going to a Python parent process.
    os.execvp(command[0], command)


if __name__ == "__main__":
    sys.exit(main())
