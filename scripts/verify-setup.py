#!/usr/bin/env python3
"""Check this machine before the board chapter, and say which targets it can run.

    python3 scripts/verify-setup.py
    python3 scripts/verify-setup.py --json     # the same findings, for a script

The point is to fail here, with a message that says what to install, rather than four chapters
in with a linker error. Nothing is fatal except a missing Python: this book has three targets and
most machines can run two of them, so an absent toolchain is reported as a target you cannot
reach yet rather than as a broken setup.

``bare`` needs nothing ``xv6`` does not — the same RISC-V cross compiler and the same
``qemu-system-riscv64`` — so it has no checks of its own and is reported alongside ``xv6``.
Anything that can run the kernel can run the bare-metal programs underneath it.

Run it on the Mac and on the board. They will report different things, and that is the answer:

    Mac / laptop / CI    bare and xv6       — structure, semantics, gdb
    A Pi or similar      all three          — and the only place a timing may be measured
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import PARTS, in_part  # noqa: E402
from bench.stamp import classify_machine, compiler_version, cpuinfo_fields  # noqa: E402


def emulated_parts() -> str:
    """``"Parts I, II and IV"`` — the parts a machine with no board can finish.

    Derived rather than typed. The line it feeds used to read "Parts III and IV", which was wrong
    in both directions once Part II existed: it claimed a part that needs the board for half its
    figures and omitted two that need nothing but QEMU.
    """
    names = [
        part.name
        for part in PARTS
        if part.page and part.target in ("bare", "xv6") and in_part(part)
    ]
    numerals = [name.removeprefix("Part ") for name in names]
    return "Parts " + ", ".join(numerals[:-1]) + f" and {numerals[-1]}"


OK, WARN, FAIL = "  ok  ", " warn ", " FAIL "

#: Cross compilers xv6's Makefile knows how to find, in the order it tries them.
CROSS_PREFIXES = ("riscv64-unknown-elf-", "riscv64-linux-gnu-", "riscv64-unknown-linux-gnu-")


class Report:
    """Findings, printable for a person and serialisable for a script."""

    def __init__(self) -> None:
        self.lines: list[tuple[str, str]] = []
        self.facts: dict[str, Any] = {}
        self.blockers: list[str] = []

    def say(self, status: str, message: str) -> None:
        self.lines.append((status, message))

    def block(self, message: str) -> None:
        self.blockers.append(message)

    def render(self) -> None:
        for status, message in self.lines:
            print(f"[{status}] {message}")


def check_python(report: Report) -> None:
    major, minor = sys.version_info[:2]
    report.facts["python"] = platform.python_version()
    if (major, minor) < (3, 11):
        report.say(FAIL, f"Python {major}.{minor} — the tooling needs 3.11 or newer")
        report.block(f"Python {major}.{minor} is too old; install 3.11+")
    else:
        report.say(OK, f"Python {major}.{minor} on {platform.machine()}")


def find_cross_compiler() -> str | None:
    for prefix in CROSS_PREFIXES:
        if shutil.which(f"{prefix}gcc"):
            return f"{prefix}gcc"
    return None


def check_xv6_target(report: Report) -> bool:
    """Can this machine build and boot the teaching kernel?"""
    print("\nTarget `xv6` — the teaching kernel under QEMU (structure, semantics, gdb)")
    ready = True

    cross = find_cross_compiler()
    if cross:
        report.say(OK, f"RISC-V cross compiler: {compiler_version(cross)}")
        report.facts["cross_cc"] = cross
    else:
        report.say(FAIL, "no RISC-V cross compiler on PATH")
        report.say(
            WARN,
            "  macOS:  brew tap riscv-software-src/riscv && brew install riscv-tools",
        )
        report.say(WARN, "  Debian/Ubuntu:  apt install gcc-riscv64-linux-gnu")
        ready = False

    if shutil.which("qemu-system-riscv64"):
        version = subprocess.run(
            ["qemu-system-riscv64", "--version"], capture_output=True, text=True, check=False
        ).stdout.splitlines()
        report.say(OK, version[0] if version else "qemu-system-riscv64 found")
        report.facts["qemu"] = version[0] if version else "unknown"
    else:
        report.say(
            FAIL, "qemu-system-riscv64 not found (brew install qemu / apt install qemu-system-misc)"
        )
        ready = False

    # `bare` needs exactly what has been checked so far and nothing below it: no kernel source,
    # no debugger. Recording it here is what lets the bare target be reported without repeating
    # a single check.
    report.facts["riscv_toolchain"] = ready

    submodule = ROOT / "xv6" / "xv6-riscv" / "Makefile"
    if submodule.exists():
        head = subprocess.run(
            ["git", "-C", str(submodule.parent), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        report.say(OK, f"xv6 submodule checked out at {head}")
        report.facts["xv6_commit"] = head
    else:
        report.say(FAIL, "xv6 submodule is empty — run `make submodule`")
        ready = False

    # Ask each candidate whether it knows the architecture rather than trusting its name. A
    # distribution's plain `gdb` is on every PATH and is usually built for the host only; it
    # connects to QEMU quite happily and then fails with `Truncated register 37 in remote 'g'
    # packet`, which is a long way from the word "gdb" being present. Appendix B sends people
    # here, so this check has to be about capability.
    found = None
    for debugger in ("gdb-multiarch", "riscv64-unknown-elf-gdb", "riscv64-elf-gdb", "gdb"):
        if not shutil.which(debugger):
            continue
        speaks_riscv = subprocess.run(
            [debugger, "-q", "-nx", "--batch", "-ex", "set architecture riscv:rv64"],
            capture_output=True,
            text=True,
            check=False,
        )
        if speaks_riscv.returncode == 0:
            found = debugger
            break
    if found:
        report.say(OK, f"debugger for the kernel: {found} (Appendix B)")
        report.facts["gdb"] = found
    else:
        report.say(
            WARN,
            "no gdb here understands riscv:rv64 — install gdb-multiarch. Appendix B needs it; "
            "nothing else does",
        )

    report.facts["xv6_ready"] = ready
    report.say(
        OK if ready else WARN,
        "target `xv6`: ready" if ready else "target `xv6`: not yet — see the lines above",
    )
    return ready


def check_bare_target(report: Report) -> bool:
    """Can this machine build and boot a program with no operating system under it?

    There is nothing to check that :func:`check_xv6_target` has not already checked: `bare` is the
    same cross compiler and the same ``qemu-system-riscv64``, with no kernel source and no
    debugger. It gets a section of its own anyway, because a reader asking whether they can start
    Part II should not have to infer the answer from a section about a kernel they are not using
    yet — and because it is genuinely *less* demanding than `xv6`, so an empty submodule stops one
    and not the other.
    """
    print("\nTarget `bare` — a RISC-V machine with no OS on it (what the hardware does)")
    ready = bool(report.facts.get("riscv_toolchain"))
    report.facts["bare_ready"] = ready
    if ready:
        report.say(OK, "shares the xv6 target's cross compiler and QEMU — nothing more to install")
        report.say(OK, "target `bare`: ready")
    else:
        report.say(WARN, "target `bare`: not yet — it needs the compiler and QEMU listed above")
    return ready


def check_host_target(report: Report) -> bool:
    """Is this the board? If not, say what this machine can and cannot stand in for."""
    print("\nTarget `host` — Linux on real hardware, natively (every number about cost)")
    kind = classify_machine()
    report.facts["machine_kind"] = kind

    if kind == "board":
        model = (
            Path("/proc/device-tree/model").read_bytes().decode(errors="replace").strip("\x00 \n")
        )
        report.say(OK, f"running natively on {model}")
        report.facts["board_model"] = model

        # The same fields a stamped result records, from the same function — so that what this
        # script prints and what the book publishes cannot come to disagree. RISC-V reports an ISA
        # string and three implementation IDs; ARM an implementer, part and feature list.
        fields = cpuinfo_fields()
        for key, value in fields.items():
            report.say(OK, f"{key}: {value}")
        report.facts["cpu"] = fields

        if shutil.which("gcc"):
            report.say(OK, f"native compiler: {compiler_version('gcc')}")
        else:
            report.say(FAIL, "no native gcc — apt install build-essential")
            report.block("the board needs build-essential")

        check_perf(report)
        report.facts["host_ready"] = True
        report.say(OK, "target `host`: ready — this machine may record timings")
        return True

    explanation = {
        "qemu": "this is a Linux guest inside QEMU, which models no cache and no pipeline",
        "qemu-user": f"this is user-mode emulation: real {platform.machine()} instructions, "
        "invented timing",
        "other": f"this is a {platform.machine()} machine, not one of the architectures the "
        "book measures on",
    }[kind]
    report.say(WARN, f"not the board: {explanation}")
    report.say(
        WARN,
        "target `host`: read-only here. Every figure in Part V is measured natively on the "
        "machine itself over SSH; `make bench-board` refuses to run anywhere else.",
    )
    report.say(WARN, "  what a board has to be able to do, and how to find one: hardware/README.md")

    # An x86-64 laptop or CI runner can still *check* RV64 code, which is most of what a
    # chapter's tests assert. Worth saying, because it is the difference between "I can work on
    # Part V from the train" and "I cannot".
    if find_cross_compiler() and (
        shutil.which("qemu-riscv64-static") or shutil.which("qemu-riscv64")
    ):
        report.say(
            OK,
            "host-target correctness path available (cross compiler + user-mode QEMU): every "
            "host example can be built and its answers checked here, just never timed",
        )
        report.facts["riscv_correctness_path"] = True
    else:
        report.say(
            WARN,
            "no host-target correctness path: install gcc-aarch64-linux-gnu and "
            "qemu-user-static to run host-target tests off the machine",
        )
        report.facts["riscv_correctness_path"] = False

    report.facts["host_ready"] = False
    return False


def check_perf(report: Report) -> None:
    """Does perf reach hardware counters on this machine?

    The one capability Part V cannot work around, which is why ch00 checks it rather than
    assuming it. On ARM the usual failure is a kernel that was never told the PMU exists; on
    RISC-V the counters arrive through the firmware's SBI PMU extension, so the answer depends on
    the firmware as much as on the core.
    """
    if not shutil.which("perf"):
        report.say(
            FAIL, "perf not installed — apt install linux-tools-common linux-tools-$(uname -r)"
        )
        report.block("Part V needs perf on the board")
        return

    probe = subprocess.run(
        ["perf", "stat", "-x,", "-e", "cycles,instructions", "--", "true"],
        capture_output=True,
        text=True,
        check=False,
    )
    counted = {}
    for line in (probe.stderr + probe.stdout).splitlines():
        fields = line.split(",")
        if len(fields) >= 3 and fields[0].strip().isdigit():
            counted[fields[2].strip()] = int(fields[0])

    if counted and all(value > 0 for value in counted.values()):
        report.say(OK, f"perf reads hardware counters: {counted}")
        report.facts["perf"] = counted
        check_sampling(report)
    else:
        report.say(FAIL, "perf ran but no event reached hardware (<not supported>)")
        report.say(
            WARN,
            "  on ARM check the device tree has a PMU node (dmesg | grep -i pmu); on RISC-V "
            "check CONFIG_RISCV_PMU_SBI and the firmware's SBI PMU extension. ch00 has both",
        )
        report.block("perf cannot read counters on this board")


def check_sampling(report: Report) -> None:
    """Counting is not sampling, and a board can do the first without the second.

    ``perf record`` needs the counters to raise an overflow interrupt, which on RISC-V means the
    Sscofpmf extension. Without it the kernel says so at boot and refuses to sample. This is not
    a failure — most of Part V counts rather than samples — but the profiling chapter is about sampling, so the
    reader is better told here than three hundred pages in.
    """
    probe = subprocess.run(
        ["perf", "record", "-q", "-o", "/dev/null", "--", "true"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (probe.stderr + probe.stdout).lower()
    can_sample = probe.returncode == 0 and "not supported" not in text
    report.facts["perf_can_sample"] = can_sample
    if can_sample:
        report.say(
            OK, "perf can sample (`perf record`) — the profiling chapter works fully on this board"
        )
    else:
        report.say(
            WARN,
            "perf counts but cannot sample (`perf record`). This needs the Sscofpmf extension, "
            "which the SiFive U74 does not have. Everything in Part V that counts is fine; "
            "the profiling chapter says what it cannot show you.",
        )


def check_book_tooling(report: Report) -> None:
    print("\nBuilding the book (optional — only needed to render the site or the PDF)")
    if shutil.which("myst"):
        version = subprocess.run(["myst", "--version"], capture_output=True, text=True, check=False)
        report.say(OK, f"mystmd {version.stdout.strip()}")
    else:
        pinned = "see package.json"
        package = ROOT / "package.json"
        if package.exists():
            data = json.loads(package.read_text())
            pinned = data.get("devDependencies", {}).get("mystmd", pinned)
        report.say(WARN, f"myst not installed (npm install -g mystmd@{pinned})")

    if shutil.which("pytest") or shutil.which("python3"):
        report.say(OK, "pytest available via `python3 -m pytest`")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    args = parser.parse_args()

    report = Report()
    if not args.json:
        print("Systems From Scratch — checking what this machine can run.\n")
    check_python(report)
    if not args.json:
        report.render()
        report.lines.clear()

    xv6_ready = check_xv6_target(report)
    if not args.json:
        report.render()
        report.lines.clear()

    bare_ready = check_bare_target(report)
    if not args.json:
        report.render()
        report.lines.clear()

    host_ready = check_host_target(report)
    if not args.json:
        report.render()
        report.lines.clear()

    check_book_tooling(report)
    if args.json:
        report.facts["blockers"] = report.blockers
        print(json.dumps(report.facts, indent=2, sort_keys=True))
        return 1 if report.blockers else 0

    report.render()
    print()
    if report.blockers:
        print("Blocked:")
        for blocker in report.blockers:
            print(f"  - {blocker}")
        return 1

    emulated = emulated_parts()
    host_part = next(part for part in PARTS if part.target == "host")
    first_host_chapter = in_part(host_part)[0].label
    if bare_ready and xv6_ready and host_ready:
        print("All three targets are available here. Start at chapter 0.")
    elif bare_ready or xv6_ready:
        print(
            f"The emulated targets are ready: {emulated} run here in full.\n"
            f"Part V is measured on real hardware; set one up before you reach "
            f"{first_host_chapter} (hardware/)."
        )
    elif host_ready:
        print(
            "This is the board: Part V runs here.\n"
            f"Install a cross compiler and QEMU to work through {emulated} as well."
        )
    else:
        print("No target is ready yet. Chapter 0 walks through all three.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
