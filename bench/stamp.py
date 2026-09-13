"""What a measured number has to carry with it before the book is allowed to print it.

The book's whole claim is that it measured things. That claim is worth exactly as much as its
weakest number, so every result written under ``bench/results/`` records five things:

* **which target** it ran on — ``host`` (the VisionFive 2 Lite, natively) or ``xv6`` (the
  teaching kernel under QEMU), because the two answer different questions and only one of them
  answers questions about time;
* **what machine** produced it — board model and ISA string, or the QEMU version and the xv6
  commit;
* **which kernel** was running;
* **which compiler and flags** built the code, because ``-O0`` and ``-O2`` are different
  experiments;
* **a content hash of the code that produced it**, so that editing the code invalidates the
  number rather than silently contradicting it.

``scripts/verify-numbers.py`` checks all five on every file in ``bench/results/`` and fails CI
when one is missing, stale, or measured somewhere it should not have been.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "bench" / "results"

#: The two execution targets. Every result declares one, and the distinction is the spine of the
#: whole book: ``xv6`` tells you what a program *does*, ``host`` tells you what it *costs*.
TARGETS = ("host", "xv6")

#: Stamps every result must carry. A number missing any of them cannot be checked by anyone,
#: including its author six months later.
REQUIRED_STAMPS = (
    "name",
    "target",
    "generated_at",
    "machine",
    "toolchain",
    "code_fingerprint",
    "code_sources",
    "summary",
)

#: Files whose contents can change a measured number no matter which runner produced it. A
#: result's fingerprint is taken over these plus the runner's own sources.
#:
#: Deliberately short. ``stamp.py`` is *not* in it: this module writes JSON and hashes bytes, and
#: cannot move a measurement, so putting it here would invalidate every result in the book each
#: time a docstring changed. ``measure.py`` *is* in it, because it decides how many repetitions a
#: figure is made of and which statistic is reported, and both change the answer.
#:
#: Chapter 14 adds the timing library (``sysfs/lib/timing.c`` and its header) to this tuple when
#: it writes one. That single edit invalidates every ``host`` result in the book, which is the
#: intended behaviour and the reason it happens once, in the chapter that introduces the clock.
CORE_SOURCES: tuple[str, ...] = ("bench/measure.py",)


class StaleFingerprintError(RuntimeError):
    """A result was produced by code that is no longer what is checked in."""


# -- the code hash -----------------------------------------------------------------------


def code_fingerprint(sources: str | list[str] | tuple[str, ...] | None = None) -> str:
    """Hash the sources a result depends on: :data:`CORE_SOURCES` plus the runner's own.

    Paths are repo-relative, so a result generated in one checkout matches the same code checked
    out anywhere else — an absolute path would make every fingerprint differ between a laptop, the
    board and CI while nothing had actually changed.

    A missing file raises rather than contributing nothing. Hashing empty bytes for a file that is
    not there turns a deleted source into a plain mismatch, and sends you hunting for a change in
    the wrong file.
    """
    if isinstance(sources, str):
        sources = [sources]
    digest = hashlib.sha256()
    for name in [*CORE_SOURCES, *(sources or ())]:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(f"cannot fingerprint missing source: {name}")
        digest.update(name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


# -- where the numbers came from ---------------------------------------------------------


def _read(path: str) -> str:
    try:
        return Path(path).read_bytes().decode(errors="replace").strip("\x00 \n")
    except OSError:
        return ""


def _cpuinfo_fields() -> dict[str, str]:
    """The RISC-V-specific lines of ``/proc/cpuinfo``, which identify the core.

    On an RV64 Linux system this carries ``isa``, ``mvendorid``, ``marchid``, ``mimpid`` and
    often ``uarch``. Those four numbers are how you tell a SiFive U74 from QEMU's generic
    implementation of the same instruction set, which matters because they execute the same
    programs at wildly different costs.
    """
    fields: dict[str, str] = {}
    for line in _read("/proc/cpuinfo").splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key in {"isa", "mvendorid", "marchid", "mimpid", "uarch", "mmu", "processor"} and value:
            fields.setdefault(key, value)
    return fields


def classify_machine() -> str:
    """``board``, ``qemu``, ``qemu-user`` or ``other`` — where this process is really running.

    This exists to stop a timing number measured in an emulator from being published as if it came
    from hardware. It is the single most valuable check in the repository, because the failure it
    prevents is invisible: emulated code produces plausible-looking timings that mean nothing.

    The signals, in order:

    * not an RV64 machine at all — a laptop or a CI runner — is ``other``;
    * RV64 with a device tree naming a real board is ``board``;
    * RV64 with a device tree naming QEMU's ``virt`` machine is ``qemu``;
    * RV64 with no device tree is user-mode emulation: ``qemu-riscv64`` fakes ``uname`` so
      :func:`platform.machine` says ``riscv64``, but there is no hardware description underneath
      because the kernel running is the host's.
    """
    if platform.machine() != "riscv64":
        return "other"
    model = _read("/proc/device-tree/model")
    if not model:
        return "qemu-user"
    lowered = model.lower()
    if "qemu" in lowered or "virtio" in lowered:
        return "qemu"
    return "board"


def describe_recorder() -> dict[str, Any]:
    """The machine running the tooling, which is not always the machine being measured.

    For a ``host`` result the two are the same board. For an ``xv6`` result the tooling runs on a
    laptop or a CI runner while the system under study is a kernel inside QEMU, so both get
    recorded and neither can be mistaken for the other.
    """
    recorder: dict[str, Any] = {
        "kind": classify_machine(),
        "arch": platform.machine(),
        "kernel": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
    }
    model = _read("/proc/device-tree/model")
    if model:
        recorder["model"] = model
    cpu = {k: v for k, v in _cpuinfo_fields().items() if k != "processor"}
    if cpu:
        recorder["cpu"] = cpu
    nproc = _read("/sys/devices/system/cpu/online")
    if nproc:
        recorder["cpus_online"] = nproc
    return recorder


def describe_board() -> dict[str, Any]:
    """The system a ``host`` result describes: this board, running this kernel.

    Every field is read from the running machine rather than from a datasheet. A spec sheet is a
    claim about a product line; ``/proc/cpuinfo`` is a statement about the silicon that produced
    the number in the table.
    """
    machine = describe_recorder()
    machine["measured_under"] = "native"
    return machine


def describe_qemu(xv6_dir: Path | None = None) -> dict[str, Any]:
    """The system an ``xv6`` result describes: xv6 at a known commit, under a known QEMU.

    ``kernel`` is the submodule's commit, not a version number, because xv6 does not have version
    numbers and the commit is what a reader would have to check out to see the same thing.
    """
    machine: dict[str, Any] = {
        "kind": "qemu",
        "arch": "riscv64",
        "model": "qemu virt (-machine virt -bios none)",
        "measured_under": "emulation",
        "emulator": qemu_version(),
        "kernel": f"xv6-riscv @ {xv6_commit(xv6_dir)}",
    }
    return machine


def qemu_version() -> str:
    binary = shutil.which("qemu-system-riscv64")
    if not binary:
        return "qemu-system-riscv64 not found"
    out = subprocess.run([binary, "--version"], capture_output=True, text=True, check=False).stdout
    return out.splitlines()[0].strip() if out else "unknown"


def xv6_commit(xv6_dir: Path | None = None) -> str:
    """The exact xv6 commit measured, so the result names something a reader can check out."""
    directory = xv6_dir or (ROOT / "xv6" / "xv6-riscv")
    out = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return out or "unknown"


def compiler_version(cc: str) -> str:
    """The compiler's own first line of ``--version``.

    Recorded verbatim. Paraphrasing it to "gcc 13" loses the distribution's patch level, and the
    distribution's patch level is exactly the kind of thing that moves a benchmark by a few per
    cent and then cannot be explained.
    """
    binary = shutil.which(cc) or cc
    out = subprocess.run([binary, "--version"], capture_output=True, text=True, check=False).stdout
    return out.splitlines()[0].strip() if out else f"{cc} (version unknown)"


# -- writing a result --------------------------------------------------------------------


def build_result(
    *,
    name: str,
    target: str,
    summary: dict[str, Any],
    code_sources: list[str] | tuple[str, ...],
    toolchain: dict[str, Any],
    machine: dict[str, Any],
    conditions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a result payload. Kept separate from writing it so tests can check the shape."""
    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}; expected one of {TARGETS}")
    return {
        "name": name,
        "target": target,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "machine": machine,
        "recorded_on": describe_recorder(),
        "toolchain": toolchain,
        "code_fingerprint": code_fingerprint(list(code_sources)),
        "code_sources": list(code_sources),
        "conditions": conditions or {},
        "summary": summary,
    }


def write_result(payload: dict[str, Any], results_dir: Path | None = None) -> Path:
    """Write one result to ``bench/results/<name>.json``, newline-terminated and sorted.

    Sorted keys and a trailing newline are not cosmetic: they make a regenerated result produce a
    minimal diff, so a reviewer can see that only the numbers moved and not the shape.
    """
    directory = results_dir or RESULTS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{payload['name']}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def load_result(name: str, results_dir: Path | None = None) -> dict[str, Any]:
    """Read one result by name, with a message that says how to regenerate it if it is missing."""
    directory = results_dir or RESULTS_DIR
    path = directory / (name if name.endswith(".json") else f"{name}.json")
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. The runner that writes it is named by "
            f"`grep -rl {Path(name).stem} bench/run_*.py`; for a host-target figure that means "
            "running `make bench-board` on the VisionFive 2."
        )
    return json.loads(path.read_text())


def flags_string(flags: list[str] | tuple[str, ...]) -> str:
    """Compiler flags as one string, for the ``toolchain.flags`` stamp and for captions."""
    return " ".join(flags)


#: Summary keys that would mean an xv6 result had recorded a duration.
_TIMING_KEYS = re.compile(
    r"(seconds|_ns$|_us$|_ms$|nanos|micros|millis|cycles|latency|elapsed|duration|"
    r"throughput|bandwidth|per_second)",
    re.IGNORECASE,
)


def _walk_keys(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        found = []
        for key, child in value.items():
            found.append(f"{prefix}{key}")
            found += _walk_keys(child, f"{prefix}{key}.")
        return found
    if isinstance(value, list):
        return [name for item in value for name in _walk_keys(item, prefix)]
    return []


def provenance_problems(name: str, payload: dict[str, Any]) -> list[str]:
    """Whether this result was measured somewhere it is allowed to have been measured.

    This is the rule the book's credibility actually rests on, so it lives beside the definition
    of a result rather than inside a script. Two claims it refuses:

    * a ``host`` figure that was not measured natively on RISC-V hardware. An emulated duration
      is indistinguishable from a real one once it is a number in a table, so the check has to
      happen where the provenance is still attached;
    * an ``xv6`` result that contains a duration at all. QEMU models no cache, no branch
      predictor and no pipeline, so a time measured inside it is not a slow measurement — it is
      not a measurement.
    """
    problems: list[str] = []
    target = payload.get("target")
    machine = payload.get("machine", {})

    if target == "host":
        if machine.get("kind") != "board":
            problems.append(
                f"{name} declares target 'host' but was produced on a "
                f"{machine.get('kind', 'unknown')!r} machine. Host figures are measured natively "
                "on the VisionFive 2 Lite; an emulated timing is not a measurement."
            )
        if machine.get("measured_under") != "native":
            problems.append(
                f"{name} declares target 'host' but records "
                f"measured_under={machine.get('measured_under')!r}, not 'native'."
            )

    if target == "xv6":
        if machine.get("kind") != "qemu":
            problems.append(
                f"{name} declares target 'xv6' but machine.kind is "
                f"{machine.get('kind')!r}, not 'qemu'."
            )
        timing = sorted(
            {key for key in _walk_keys(payload.get("summary", {})) if _TIMING_KEYS.search(key)}
        )
        if timing:
            problems.append(
                f"{name} is an xv6 result carrying what looks like a timing: "
                f"{', '.join(timing)}. QEMU models no cache, no predictor and no pipeline, so a "
                "duration measured inside it means nothing — move the measurement to the board."
            )

    return problems


def normalise_isa(isa: str) -> str:
    """Lower-case an ISA string and drop whitespace, so two spellings of the same ISA compare."""
    return re.sub(r"\s+", "", isa.lower())
