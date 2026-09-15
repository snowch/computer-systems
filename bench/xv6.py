"""Booting xv6 under QEMU and driving its shell, so an ``xv6`` example can be checked by CI.

The xv6 target answers questions about *structure*: what a system call does, how a page table is
walked, what happens in ``exec``. It answers no questions about time at all, and this module
refuses to pretend otherwise — there is nothing here that returns a duration. QEMU executes
instructions correctly and models nothing about the cost of executing them: no caches, no branch
predictor, no memory latency, no pipeline. A loop that runs in 40 ns on the board and a loop that
runs in 4 µs take the same number of "QEMU seconds", and those seconds depend mostly on the
laptop QEMU is running on.

## The staging tree

The submodule at ``xv6/xv6-riscv`` is upstream, and stays that way: never a modified copy. To
build, :func:`prepare` copies it to ``xv6/stage`` and applies the book's own material there —

* ``xv6/apps/*.c`` become xv6 user programs, registered in the staged Makefile automatically;
* ``sysfs/include/sysfs/*.h`` are copied to ``sysfs/`` inside the staging tree, so a program can
  ``#include "sysfs/probe.h"`` and get the same bytes the board compiles — xv6 already builds
  with ``-I.``, so nothing has to be added to its flags;
* ``xv6/patches/*.patch`` are the book's kernel instrumentation, applied in filename order.

so the submodule never goes dirty, a failed patch cannot leave a half-modified kernel behind, and
``git submodule status`` stays a statement about upstream rather than about us.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import signal
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from bench.stamp import ROOT

XV6_SUBMODULE = ROOT / "xv6" / "xv6-riscv"
APPS_DIR = ROOT / "xv6" / "apps"
SHARED_HEADERS = ROOT / "sysfs" / "include" / "sysfs"
PATCHES_DIR = ROOT / "xv6" / "patches"
STAGE = ROOT / "xv6" / "stage"

#: xv6's shell prompt. Everything here is a search for this two-character string.
PROMPT = "$ "

#: Default core count. Three, matching upstream's own default, and enough that ch12 and ch13 have
#: something to say about concurrency while a boot still takes about a second.
DEFAULT_CPUS = 3


class Xv6UnavailableError(RuntimeError):
    """The xv6 target cannot run here: no QEMU, or the submodule was never checked out."""


def missing_requirements() -> list[str]:
    """What is stopping the xv6 target from running, in words a reader can act on."""
    problems = []
    if not shutil.which("qemu-system-riscv64"):
        problems.append("qemu-system-riscv64 is not installed (see ch00)")
    if not (XV6_SUBMODULE / "Makefile").exists():
        problems.append("the xv6 submodule is empty (git submodule update --init --recursive)")
    if not (shutil.which("riscv64-linux-gnu-gcc") or shutil.which("riscv64-unknown-elf-gcc")):
        problems.append("no RISC-V cross compiler on PATH (see ch00)")
    return problems


def available() -> bool:
    return not missing_requirements()


def require() -> None:
    problems = missing_requirements()
    if problems:
        raise Xv6UnavailableError("; ".join(problems))


# -- staging -----------------------------------------------------------------------------


def _inputs_digest(extra_apps: Sequence[Path] = ()) -> str:
    """A hash of everything that decides what the staged tree contains.

    The submodule commit, plus the bytes of every app and patch. Staging is skipped when this has
    not changed, which turns a 30-second rebuild into nothing on the common path — and, more
    usefully, makes "did my patch get applied?" a question with a definite answer.
    """
    digest = hashlib.sha256()
    head = subprocess.run(
        ["git", "-C", str(XV6_SUBMODULE), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    digest.update(head.encode())
    sources = (
        sorted(APPS_DIR.glob("*.c"))
        + sorted(PATCHES_DIR.glob("*.patch"))
        + sorted(SHARED_HEADERS.glob("*.h"))
    )
    for path in [*sources, *extra_apps]:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _register_apps(makefile: Path, apps: list[str]) -> None:
    """Add the book's programs to the staged Makefile's ``UPROGS``.

    Done mechanically rather than by a patch. A patch against a list of filenames breaks the next
    time upstream adds a program of its own, and the failure ("does not apply") tells you nothing
    about what you actually wanted; inserting a line in front of a known marker does not.
    """
    text = makefile.read_text()
    marker = "UPROGS=\\\n"
    if marker not in text:
        raise RuntimeError(f"{makefile} has no UPROGS list — upstream changed shape")
    additions = "".join(f"\t$U/_{name}\\\n" for name in sorted(apps))
    makefile.write_text(text.replace(marker, marker + additions, 1))


def prepare(force: bool = False, extra_apps: Sequence[Path] = ()) -> Path:
    """Stage xv6 plus the book's material into ``xv6/stage`` and return that directory.

    ``extra_apps`` stages user programs that are not part of the normal build — the reader's
    answers to a chapter's problems, which live under ``tests/`` precisely so that an unfinished
    one cannot break everybody's kernel.
    """
    require()
    digest = _inputs_digest(extra_apps)
    stamp = STAGE / ".stage-stamp"
    if not force and stamp.exists() and stamp.read_text().strip() == digest:
        return STAGE

    if STAGE.exists():
        shutil.rmtree(STAGE)
    shutil.copytree(
        XV6_SUBMODULE, STAGE, ignore=shutil.ignore_patterns(".git", "*.o", "*.d", "*.asm", "*.sym")
    )

    if SHARED_HEADERS.is_dir():
        shutil.copytree(SHARED_HEADERS, STAGE / "sysfs", dirs_exist_ok=True)

    apps = []
    for source in [*sorted(APPS_DIR.glob("*.c")), *extra_apps]:
        shutil.copy2(source, STAGE / "user" / source.name)
        apps.append(source.stem)
    if apps:
        _register_apps(STAGE / "Makefile", apps)

    for patch in sorted(PATCHES_DIR.glob("*.patch")):
        result = subprocess.run(
            ["git", "apply", "--verbose", str(patch)],
            cwd=STAGE,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"{patch.name} does not apply to xv6 @ {_inputs_digest()}:\n{result.stderr}\n"
                "Upstream has moved; regenerate the patch against the current submodule commit."
            )

    stamp.write_text(digest + "\n")
    return STAGE


def build(
    cpus: int = DEFAULT_CPUS, jobs: int | None = None, extra_apps: Sequence[Path] = ()
) -> Path:
    """Build the staged kernel and file system image. Returns the staging directory."""
    stage = prepare(extra_apps=extra_apps)
    jobs = jobs or (os.cpu_count() or 2)
    result = subprocess.run(
        ["make", f"-j{jobs}", f"CPUS={cpus}", "kernel/kernel", "fs.img"],
        cwd=stage,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"building xv6 failed:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
        )
    return stage


def qemu_command(stage: Path, cpus: int = DEFAULT_CPUS, memory: str = "128M") -> list[str]:
    """The QEMU invocation, spelled out rather than delegated to xv6's ``make qemu``.

    Upstream's target is written for a person at a terminal: it takes over the console and has no
    way to say "run these commands and tell me what happened". Building the command here is what
    lets a test boot the kernel, type into it, and assert on the output.
    """
    return [
        "qemu-system-riscv64",
        "-machine",
        "virt",
        "-bios",
        "none",
        "-kernel",
        str(stage / "kernel" / "kernel"),
        "-m",
        memory,
        "-smp",
        str(cpus),
        "-nographic",
        "-global",
        "virtio-mmio.force-legacy=false",
        "-drive",
        # snapshot=on: writes go to a temporary overlay and the image on disk is never touched,
        # so every boot starts from the same filesystem. Without it a measurement that writes a
        # file would depend on how many times the suite had been run since `mkfs` last ran — and
        # while QEMU does not in fact flush this image before it is killed, "the emulator happens
        # not to get round to it" is not a property to record numbers against. ch11 counts disk
        # interrupts, which is what made the question worth settling rather than assuming.
        f"file={stage / 'fs.img'},if=none,format=raw,id=x0,snapshot=on",
        "-device",
        "virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0",
    ]


@dataclass
class BootResult:
    """Everything the console said, and what was typed into it."""

    transcript: str
    commands: list[str] = field(default_factory=list)
    timed_out: bool = False
    cpus: int = DEFAULT_CPUS

    def output_of(self, command: str) -> str:
        """The lines a command printed, with the shell's echo of the command itself removed.

        xv6's console echoes what you type, so the transcript contains the command followed by its
        output followed by the next prompt. Slicing between those is what turns a console recording
        into something a test can assert on.
        """
        marker = command + "\n"
        start = self.transcript.find(marker)
        if start < 0:
            raise AssertionError(f"{command!r} was never echoed; transcript:\n{self.transcript}")
        start += len(marker)
        end = self.transcript.find(PROMPT, start)
        return self.transcript[start : end if end >= 0 else None].strip()


def boot(
    commands: list[str] | None = None,
    *,
    cpus: int = DEFAULT_CPUS,
    timeout: float = 90.0,
    settle: float = 0.6,
    extra_apps: Sequence[Path] = (),
) -> BootResult:
    """Boot xv6, type ``commands`` at its shell, and return the whole console transcript.

    QEMU is started in its own process group and killed by group at the end. xv6 has no way to
    shut the machine down from its shell, so the only exit is to stop the emulator; killing the
    group rather than the process means a QEMU that has forked helpers does not leave one behind
    holding the terminal.
    """
    require()
    stage = build(cpus=cpus, extra_apps=extra_apps)
    commands = list(commands or [])

    process = subprocess.Popen(
        qemu_command(stage, cpus=cpus),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    assert process.stdout is not None and process.stdin is not None
    os.set_blocking(process.stdout.fileno(), False)

    transcript = ""
    pending = list(commands)
    # One prompt for the shell starting, then one after each command completes.
    wanted_prompts = len(commands) + 1
    deadline = time.time() + timeout
    timed_out = True

    try:
        while time.time() < deadline:
            chunk = process.stdout.read(65536)
            if chunk:
                transcript += chunk.decode(errors="replace")
            seen = transcript.count(PROMPT)
            if pending and seen >= len(commands) - len(pending) + 1:
                process.stdin.write((pending.pop(0) + "\n").encode())
                process.stdin.flush()
            elif not pending and seen >= wanted_prompts:
                # Let anything still in flight arrive before the emulator is killed; without this
                # the last command's final line is lost about one run in twenty.
                time.sleep(settle)
                chunk = process.stdout.read(1 << 20)
                if chunk:
                    transcript += chunk.decode(errors="replace")
                timed_out = False
                break
            time.sleep(0.02)
    finally:
        # A kernel panic makes QEMU exit on its own, so the process may already be gone. Suppress
        # that race explicitly: a test that reports ProcessLookupError instead of "the kernel
        # panicked" wastes an afternoon.
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        process.wait(timeout=10)

    return BootResult(transcript=transcript, commands=commands, timed_out=timed_out, cpus=cpus)
