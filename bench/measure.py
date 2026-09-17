"""Building and running the book's C, and turning repeated runs into one reportable number.

This module is in :data:`bench.stamp.CORE_SOURCES`, which means changing it invalidates every
committed result. That is on purpose. Two decisions live here and both change what a measurement
means: **where the code runs**, and **which statistic the book prints**.

## Where the code runs

There are three ways to execute the book's ``host``-target C, and only one of them may be timed:

============================  ===================================  =================
How                           What it is good for                  Timing?
============================  ===================================  =================
Natively on the machine       everything the book claims            **yes**
Cross-compiled, ``qemu-user`` target semantics: ABI, sizes, encoding no
Natively on a laptop          C portability, test logic             no
============================  ===================================  =================

CI is an x86-64 runner, so it takes the middle row: it proves that every example compiles for
RV64 and produces the right answer, and it never produces a timing. :func:`resolve_host_target`
picks the row and, more importantly, labels it, so the decision cannot be made by accident.

## Which statistic

A benchmark's samples are not a normal distribution around a "true" value. They are a floor —
the fastest the machine can do the work — plus interference: interrupts, migrations, another
process, a TLB shootdown. Interference only ever adds. So the book reports the **minimum** as the
best case the hardware can achieve, the **median** as what a caller typically sees, and a high
percentile as the tail, and it never reports a mean, which is a number nobody experiences and
which a single scheduling hiccup can move. The measurement chapter makes this argument properly
and measures the distribution that justifies it.
"""

from __future__ import annotations

import platform
import shutil
import statistics
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bench.stamp import ROOT, classify_machine, compiler_version, flags_string

#: Flags every build starts from, whatever it is building for.
COMMON_FLAGS: tuple[str, ...] = ("-O2", "-g", "-Wall", "-Wextra")

#: Architecture flags, by target architecture.
#:
#: AArch64 gets none: the baseline is armv8-a and naming a specific core would bake the
#: reference machine into every binary, which is exactly the mistake the setup chapter stopped
#: making about boards. RISC-V gets an explicit ``-march``/``-mabi`` because the default varies by
#: distribution, and a silently different ABI is a very confusing way to lose an afternoon.
ARCH_FLAGS: dict[str, tuple[str, ...]] = {
    "aarch64": (),
    "riscv64": ("-march=rv64gc", "-mabi=lp64d"),
}

#: What a laptop or CI runner can be asked to build when the point is the C and not the ISA.
PORTABLE_FLAGS: tuple[str, ...] = COMMON_FLAGS


def flags_for(arch: str) -> tuple[str, ...]:
    return (*COMMON_FLAGS, *ARCH_FLAGS.get(arch, ()))


class ToolchainMissingError(RuntimeError):
    """No compiler that can produce code for the requested target."""


@dataclass(frozen=True)
class HostTarget:
    """How to build and run ``host``-target C *here*, and whether the result may be timed.

    ``trustworthy_for_timing`` is the whole point of this type. Every other field describes how to
    get an answer; this one says whether the answer is allowed to be a number of nanoseconds.
    """

    name: str
    cc: str
    flags: tuple[str, ...]
    runner: tuple[str, ...] = ()
    trustworthy_for_timing: bool = False
    why: str = ""

    def stamp(self) -> dict[str, Any]:
        """The ``toolchain`` block for a result produced with this target."""
        block: dict[str, Any] = {
            "cc": compiler_version(self.cc),
            "flags": flags_string(self.flags),
            "execution": self.name,
        }
        if self.runner:
            block["runner"] = " ".join(self.runner)
        return block


def resolve_host_target(prefer_portable: bool = False) -> HostTarget:
    """Decide how ``host``-target C can be built and run on this machine.

    Order matters. Real hardware first, because if a board is here that is always the right
    answer — and note that it does not matter *which* board: a Raspberry Pi and a VisionFive 2
    are both places a timing means something, and both are recorded by name in the result.

    Then cross-compilation with user-mode emulation, which gets the reference architecture's
    semantics onto an x86-64 CI runner. AArch64 is tried before RISC-V because the reference
    machine is a Pi; the RISC-V path stays because Parts III and IV need that toolchain anyway and
    a reader following Part V on a RISC-V board should have their examples checked too.

    Then the plain native compiler, which exercises the test logic and nothing else.
    """
    if classify_machine() == "board":
        arch = platform.machine()
        return HostTarget(
            name=f"native-{arch}",
            cc="gcc",
            flags=flags_for(arch),
            trustworthy_for_timing=True,
            why=f"running natively on {arch} hardware",
        )

    for arch, prefix in (("aarch64", "aarch64-linux-gnu-"), ("riscv64", "riscv64-linux-gnu-")):
        cross = shutil.which(f"{prefix}gcc")
        emulator = shutil.which(f"qemu-{arch}-static") or shutil.which(f"qemu-{arch}")
        if cross and emulator:
            return HostTarget(
                name=f"cross-{arch}-qemu",
                cc=f"{prefix}gcc",
                # -static, and only here. User-mode QEMU runs the binary against the *host* file
                # system, so a dynamically linked binary asks for a loader an x86-64 machine does
                # not have. Linking statically sidesteps it. It is also a reminder of what this
                # row is for: nobody would time a statically linked binary against a dynamic one
                # and call it the same experiment, and nothing here is timed.
                flags=(*flags_for(arch), "-static"),
                runner=(emulator,),
                trustworthy_for_timing=False,
                why=f"user-mode emulation: real {arch} instructions, invented timing",
            )

    if prefer_portable or shutil.which("cc"):
        return HostTarget(
            name="native-other",
            cc="cc",
            flags=PORTABLE_FLAGS,
            trustworthy_for_timing=False,
            why=f"a {platform.machine()} machine, not the reference architecture: this checks "
            "the C, not the hardware",
        )

    raise ToolchainMissingError(
        "no usable C compiler. Install one, or on a laptop install gcc-aarch64-linux-gnu and "
        "qemu-user-static to run the host-target correctness path."
    )


@dataclass
class Built:
    """A compiled program, and the command that produced it."""

    path: Path
    command: list[str] = field(default_factory=list)
    target: HostTarget | None = None

    def run(self, args: Sequence[str] = (), **kwargs: Any) -> subprocess.CompletedProcess[str]:
        runner = list(self.target.runner) if self.target else []
        return subprocess.run(
            [*runner, str(self.path), *args],
            capture_output=True,
            text=True,
            check=kwargs.pop("check", True),
            **kwargs,
        )


def compile_program(
    sources: Sequence[str | Path],
    output: str | Path,
    target: HostTarget,
    *,
    extra_flags: Sequence[str] = (),
    includes: Sequence[str | Path] = (),
) -> Built:
    """Compile C for the given host target, raising with the compiler's own message on failure.

    Paths are resolved against the repository root so a runner works from any directory, and the
    output directory is created rather than assumed.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        target.cc,
        *target.flags,
        *extra_flags,
        *[f"-I{Path(inc) if Path(inc).is_absolute() else ROOT / inc}" for inc in includes],
        *[str(Path(s) if Path(s).is_absolute() else ROOT / s) for s in sources],
        "-o",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"compiling {[str(s) for s in sources]} failed with {target.cc}:\n{result.stderr}"
        )
    return Built(path=output, command=command, target=target)


# -- turning repeated runs into one number -----------------------------------------------


def repeat(work: Callable[[], float], n: int, warmup: int = 0) -> list[float]:
    """Run ``work`` ``n`` times and keep every sample.

    Every sample, not a running mean: the distribution is the interesting part, and a summary
    computed on the fly cannot be re-examined once you notice the shape is wrong.
    """
    for _ in range(warmup):
        work()
    return [work() for _ in range(n)]


def summarise(samples: Sequence[float]) -> dict[str, Any]:
    """Reduce samples to what the book prints: a floor, a typical case, and a tail.

    No mean. See this module's docstring, and the measurement chapter for the figure that
    settles it.
    """
    if not samples:
        raise ValueError("cannot summarise an empty sample set")
    ordered = sorted(samples)
    return {
        "n": len(ordered),
        "min": ordered[0],
        "median": statistics.median(ordered),
        "p90": _percentile(ordered, 0.90),
        "p99": _percentile(ordered, 0.99),
        "max": ordered[-1],
        # Spread relative to the floor. A run where this is large is a run where something else
        # was happening on the machine, and the chapter has to say so rather than average it away.
        "spread_over_min": (ordered[-1] / ordered[0]) if ordered[0] else None,
    }


def _percentile(ordered: Sequence[float], q: float) -> float:
    """Nearest-rank percentile on an already-sorted sequence.

    Nearest-rank rather than interpolated, because an interpolated p99 reports a value that was
    never measured, and the book's claim is that it measured things.
    """
    if not ordered:
        raise ValueError("empty sequence")
    index = max(0, min(len(ordered) - 1, round(q * len(ordered) + 0.5) - 1))
    return ordered[index]
