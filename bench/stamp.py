"""What a measured number has to carry with it before the book is allowed to print it.

The book's whole claim is that it measured things. That claim is worth exactly as much as its
weakest number, so every result written under ``bench/results/`` records five things:

* **which target** it ran on — ``host`` (real hardware, natively) or ``xv6`` (the
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

A result also declares its **kind**. Almost every one is a ``measurement``; a ``listing`` is
disassembly captured from a compiler so a chapter can show machine code without pasting it. The
two are held to different rules and neither set would be right for the other — see :data:`KINDS`.
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

#: What a result *is*. Nearly all of them are measurements — a machine was asked a question and
#: this is what it answered. A ``listing`` is different in kind: it is what a compiler emitted,
#: captured so that a chapter can show machine code without pasting it (``bench/disasm.py``).
#:
#: The distinction earns its place because the two have opposite provenance rules. A measurement's
#: worth depends entirely on *where* it was taken, which is why a ``host`` figure must come from
#: the board. A listing does not depend on the machine at all — the same compiler and flags give
#: the same instructions on a laptop, on CI and on the board — so demanding a board for one would
#: be theatre. In exchange a listing must carry no timings whatsoever, on either target: it is
#: evidence about what the compiler chose, and never about what that choice cost.
#:
#: An ``artefact`` is the same bargain for everything else a toolchain produces and the book
#: *describes* rather than quotes: section sizes, symbol tables, what survives each stage. It is
#: separate from ``listing`` rather than folded into it because a listing is reproduced verbatim
#: into a chapter and therefore has a shape worth enforcing, while an artefact's summary is
#: whatever that chapter needed to count. Both are held to the rule that matters: no durations.
KINDS = ("measurement", "listing", "artefact")

#: The kinds a compiler produces rather than a machine. Exempt from the board rule, and in
#: exchange forbidden from carrying a timing at all.
COMPILED_KINDS = ("listing", "artefact")

#: Architectures a ``host`` figure may be measured on.
#:
#: The two targets no longer share an instruction set, and that is a deliberate choice rather
#: than an accident. ``xv6`` is RISC-V because the kernel that can be read in an afternoon is a
#: RISC-V kernel; ``host`` is AArch64 because that is where the performance counters actually
#: work — RISC-V's overflow-interrupt support is absent on every affordable in-order core, which
#: makes sampling impossible and a profiling chapter unwritable.
#:
#: ``riscv64`` stays permitted because a reader who already owns a RISC-V board can follow Part
#: III on it, with the limits each chapter names in its own header.
BOARD_ARCHES = ("aarch64", "riscv64")

#: Stamps every result must carry. A number missing any of them cannot be checked by anyone,
#: including its author six months later.
REQUIRED_STAMPS = (
    "name",
    "target",
    "kind",
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

#: Sources that are core to *one target only*, keyed by target.
#:
#: ch14 adds the book's clock, through which every duration in Part III is read — so a change to
#: it changes what every `host` figure means, and belongs in those figures' fingerprints. It does
#: not belong in an xv6 result's: a page-table census does not depend on how the book tells the
#: time, and putting it in CORE_SOURCES made every structural result in Parts I and II churn the
#: moment the clock was touched. The plan said that would happen once. It would in fact have
#: happened on every edit to the clock for the rest of the book, which is the kind of noise that
#: teaches people to re-stamp without reading what moved.
TARGET_SOURCES: dict[str, tuple[str, ...]] = {
    "host": ("sysfs/lib/timing.c", "sysfs/include/sysfs/timing.h"),
}


class StaleFingerprintError(RuntimeError):
    """A result was produced by code that is no longer what is checked in."""


# -- the code hash -----------------------------------------------------------------------


def code_fingerprint(
    sources: str | list[str] | tuple[str, ...] | None = None, target: str | None = None
) -> str:
    """Hash the sources a result depends on.

    :data:`CORE_SOURCES`, plus whatever :data:`TARGET_SOURCES` says is core to this target, plus
    the runner's own.

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
    for name in [*CORE_SOURCES, *TARGET_SOURCES.get(target or "", ()), *(sources or ())]:
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


#: ``/proc/cpuinfo`` keys that identify the core, on either architecture. RISC-V reports an ISA
#: string and three vendor/architecture/implementation IDs; ARM reports an implementer, part and
#: revision plus a feature list. Both are how you tell one core from another implementation of
#: the same instruction set — which matters, because they run the same programs at very
#: different costs.
_CPU_KEYS = frozenset(
    {
        # RISC-V
        "isa",
        "mvendorid",
        "marchid",
        "mimpid",
        "uarch",
        "mmu",
        # ARM
        "cpu implementer",
        "cpu architecture",
        "cpu variant",
        "cpu part",
        "cpu revision",
        "features",
        "model name",
        "bogomips",
    }
)


def cpuinfo_fields() -> dict[str, str]:
    """The lines of ``/proc/cpuinfo`` that identify the core, whichever architecture it is.

    Public because ``scripts/verify-setup.py`` prints the same fields a result records. Two
    separate lists of interesting keys would drift, and the first sign of it would be a setup
    script confidently reporting nothing at all about a core.
    """
    fields: dict[str, str] = {}
    for line in _read("/proc/cpuinfo").splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key in _CPU_KEYS and value:
            fields.setdefault(key, value)
    return fields


def _os_release() -> str:
    """The distribution and version, as the running system describes itself.

    Recorded because the kernel alone is not the whole configuration. The reference machine's
    counters went missing for a kernel release — the Pi 5's device tree dropped the ``arm-pmu``
    node in 6.12.y @rpi-pmu-dt-6507 — so "which image, which kernel" is part of what a ``host``
    result means, and a reader comparing their numbers with the book's needs both.
    """
    for line in _read("/etc/os-release").splitlines():
        key, _, value = line.partition("=")
        if key == "PRETTY_NAME":
            return value.strip().strip('"')
    return ""


def classify_machine() -> str:
    """``board``, ``qemu``, ``qemu-user`` or ``other`` — where this process is really running.

    This exists to stop a timing number measured in an emulator from being published as if it came
    from hardware. It is the single most valuable check in the repository, because the failure it
    prevents is invisible: emulated code produces plausible-looking timings that mean nothing.

    The signals, in order:

    * not a board architecture at all — an x86-64 laptop or CI runner — is ``other``;
    * a board architecture with a device tree naming real hardware is ``board``;
    * a board architecture with a device tree naming QEMU's ``virt`` machine is ``qemu``;
    * a board architecture with no device tree is user-mode emulation: ``qemu-aarch64`` and
      ``qemu-riscv64`` both fake ``uname``, so :func:`platform.machine` reports the target
      architecture while the kernel underneath is the host's and there is no hardware
      description at all.
    """
    if platform.machine() not in BOARD_ARCHES:
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
    distribution = _os_release()
    if distribution:
        recorder["os"] = distribution
    cpu = {k: v for k, v in cpuinfo_fields().items() if k != "processor"}
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


def describe_toolchain(arch: str) -> dict[str, Any]:
    """The "machine" of a listing, which is a compiler rather than a computer.

    Every other result answers a question a machine was asked, so its machine block says which
    computer. A listing answers a question the *compiler* was asked, and the honest answer to
    "where was this produced" is anywhere: same compiler, same flags, same instructions. Saying so
    explicitly is better than leaving the field out, because it puts the reason in the result,
    where the next person to wonder why CI is allowed to regenerate this will find it.
    """
    return {
        "kind": "toolchain",
        "arch": arch,
        "measured_under": "compilation",
        "model": f"{arch} cross compiler, any machine — nothing here was executed",
    }


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
    kind: str = "measurement",
) -> dict[str, Any]:
    """Assemble a result payload. Kept separate from writing it so tests can check the shape."""
    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}; expected one of {TARGETS}")
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; expected one of {KINDS}")
    return {
        "name": name,
        "target": target,
        "kind": kind,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "machine": machine,
        "recorded_on": describe_recorder(),
        "toolchain": toolchain,
        "code_fingerprint": code_fingerprint(list(code_sources), target),
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
            "running `make bench-board` on the machine being measured."
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


def timing_keys(summary: Any) -> list[str]:
    """Summary keys that look like a duration, wherever they are nested."""
    return sorted({key for key in _walk_keys(summary) if _TIMING_KEYS.search(key)})


def _compiled_problems(name: str, payload: dict[str, Any], kind: str) -> list[str]:
    """What a compiler-produced result has to be, given that it skips the board rule.

    The exemption is sound — instructions and section sizes do not depend on which computer ran
    the compiler — but it is also the one loophole in the whole scheme: a timing relabelled
    ``kind: listing`` would walk straight past the check that exists to stop exactly that. So one
    of these has to look like one. It carries no durations on either target, and it says outright
    that nothing was executed.
    """
    problems: list[str] = []
    machine = payload.get("machine", {})
    summary = payload.get("summary", {})

    if machine.get("measured_under") != "compilation":
        problems.append(
            f"{name} is a {kind} but records measured_under="
            f"{machine.get('measured_under')!r}. It is compiled, not run."
        )

    timing = timing_keys(summary)
    if timing:
        problems.append(
            f"{name} is a {kind} carrying what looks like a timing: {', '.join(timing)}. This is "
            "evidence about what the compiler produced, never about what it cost — record the "
            "cost as a host measurement on the board instead."
        )

    if kind == "artefact":
        if not summary:
            problems.append(f"{name} is an artefact with an empty summary")
        return problems

    listings = summary.get("listings")
    if not isinstance(listings, dict) or not listings:
        problems.append(f"{name} is a listing but its summary has no 'listings' mapping")
        return problems

    for symbol, entry in sorted(listings.items()):
        if not isinstance(entry, dict) or set(entry) != {"symbol", "text", "instructions"}:
            problems.append(
                f"{name}: listing {symbol!r} is not shaped like one "
                "(expected exactly symbol, text and instructions)"
            )
        elif not str(entry.get("text", "")).strip():
            problems.append(f"{name}: listing {symbol!r} is empty")

    return problems


def provenance_problems(name: str, payload: dict[str, Any]) -> list[str]:
    """Whether this result was produced somewhere it is allowed to have been produced.

    This is the rule the book's credibility actually rests on, so it lives beside the definition
    of a result rather than inside a script. Three claims it refuses:

    * a ``host`` measurement that was not taken natively on the board. An emulated duration is
      indistinguishable from a real one once it is a number in a table, so the check has to happen
      while the provenance is still attached;
    * an ``xv6`` result that contains a duration at all. QEMU models no cache, no branch
      predictor and no pipeline, so a time measured inside it is not a slow measurement — it is
      not a measurement;
    * a ``listing`` that is anything other than disassembly. Listings are exempt from the first
      rule, so they have to be held to their own.

    A result with no ``kind`` is a measurement. That was the only thing a result could be when the
    field did not exist, and reading it that way means an old file is judged by the stricter rules
    rather than slipping past both.
    """
    problems: list[str] = []
    target = payload.get("target")
    machine = payload.get("machine", {})
    kind = payload.get("kind", "measurement")

    if kind not in KINDS:
        return [f"{name} declares kind {kind!r}, which is not one of {KINDS}"]
    if kind in COMPILED_KINDS:
        return _compiled_problems(name, payload, kind)

    if target == "host":
        if machine.get("kind") != "board":
            problems.append(
                f"{name} declares target 'host' but was produced on a "
                f"{machine.get('kind', 'unknown')!r} machine. Host figures are measured "
                "natively on the reference machine; an emulated timing is not a measurement."
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
        timing = timing_keys(payload.get("summary", {}))
        if timing:
            problems.append(
                f"{name} is an xv6 result carrying what looks like a timing: "
                f"{', '.join(timing)}. QEMU models no cache, no predictor and no pipeline, so a "
                "duration measured inside it means nothing — move the measurement to the board."
            )

    return problems


def measurement_differences(committed: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    """What actually changed between two runs of the same measurement.

    **The measurement is the summary.** Everything else in a result is provenance, and provenance
    is policed separately by ``scripts/verify-numbers.py`` — stamps present, code fingerprint
    matching, target measured somewhere it was allowed to be. Re-running answers one question
    only: *do we still get the same answers?*

    So everything outside the summary is ignored, and each part of it for its own reason:

    * ``generated_at`` changes on every run by definition, and ``recorded_on`` describes the
      machine that drove the tooling — for an ``xv6`` result a laptop or a CI runner, not the
      system under study. Comparing whole files byte-for-byte counts both, which reports a
      difference every time, including on the same machine a second later.
    * ``machine`` and ``toolchain`` are context. A runner whose QEMU or compiler is a version
      ahead still agrees about the answers, and failing on that would make this check noise.
      A noisy check gets ignored, which costs more than it saves.

    A difference in the summary is worth failing over even when its cause is a toolchain change,
    because the committed result is then stale and the table rendered from it is showing a figure
    the code no longer produces. The fix is the same either way: re-run and commit.
    """
    return _compare(committed.get("summary", {}), fresh.get("summary", {}), "summary")


def _compare(before: Any, after: Any, path: str) -> list[str]:
    if isinstance(before, dict) and isinstance(after, dict):
        differences = []
        for key in sorted(set(before) | set(after)):
            if key not in before:
                differences.append(f"{path}.{key}: added, now {after[key]!r}")
            elif key not in after:
                differences.append(f"{path}.{key}: gone, was {before[key]!r}")
            else:
                differences += _compare(before[key], after[key], f"{path}.{key}")
        return differences
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            return [f"{path}: {len(before)} entries, now {len(after)}"]
        return [
            difference
            for index, (old, new) in enumerate(zip(before, after, strict=True))
            for difference in _compare(old, new, f"{path}[{index}]")
        ]
    return [] if before == after else [f"{path}: {before!r}, now {after!r}"]


def normalise_isa(isa: str) -> str:
    """Lower-case an ISA string and drop whitespace, so two spellings of the same ISA compare."""
    return re.sub(r"\s+", "", isa.lower())
