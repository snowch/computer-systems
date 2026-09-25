"""How wrong a number is: the spread around it, and whether two of them really differ.

Part V reports durations. This module is what turns a pile of samples into something a chapter
may print, and it exists because the measurement chapter's own argument needs it: a single
duration is an anecdote, a median without a spread is a claim with the uncertainty deleted, and
"B is faster than A" is not an observation until somebody says how much difference would have
been enough.

Three things live here and nothing else does.

**A confidence interval on the median, by bootstrap.** Resample the samples you have, with
replacement, take the median of each resample, and look at where the middle of those medians
falls. It assumes only that the runs are exchangeable, which is weaker than assuming a shape —
and it is wrong in a way the chapter has to state, because runs that drift are not exchangeable.

**A decision rule.** Two configurations differ only if the interval on the difference excludes
zero *and* the difference is bigger than a threshold stated in advance. Both halves matter: the
first is about evidence and the second is about whether anybody would care.

**The environment a timing was taken in.** Governor, frequency, which CPU, what else was
running, and the temperature if the board will say. These change a number more than most of the
code in this book does, so they are recorded beside it rather than remembered.

## Why no numpy

`requirements.txt` has one entry and says why. A bootstrap is a loop over `random.choices` and a
median, both in the standard library; importing an array library to avoid writing fifteen lines
would buy speed this does not need and cost a dependency the book would then have to pin,
justify and keep working. The resample count and the seed are recorded in the stamp, so the
interval is reproducible without one.

## Why this is not in `measure.py`

`bench/measure.py` is in :data:`bench.stamp.CORE_SOURCES`, so every committed result in the book
carries a hash of it. Putting this here instead means adding a confidence interval to the book
does not invalidate a single existing measurement — which matters, because fifteen of them were
taken on a board that is not always attached, and a fingerprint they cannot answer is a red
build nobody can fix from a laptop.
"""

from __future__ import annotations

import os
import random
import statistics
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

#: How many resamples a published interval is built from.
#:
#: Enough that the interval's own wobble is well below the interval, and small enough to run in a
#: second of pure Python. It is recorded in every stamp rather than assumed, so a figure taken at
#: a different count is still readable.
RESAMPLES = 2000

#: The seed every published interval uses.
#:
#: A bootstrap is random, and a figure that moved every time it was regenerated could not be
#: checked for staleness — which is the mechanism the whole book's results rest on. Fixing the
#: seed makes the interval a deterministic function of the samples. It does not make the interval
#: more true, and the chapter says so.
SEED = 20260925

Mode = Literal["cold", "warm"]


# -- the interval ------------------------------------------------------------------------


def bootstrap_median_ci(
    samples: Sequence[float],
    *,
    resamples: int = RESAMPLES,
    seed: int = SEED,
    confidence: float = 0.90,
) -> tuple[float, float]:
    """A percentile-bootstrap interval on the median of ``samples``.

    Draw ``resamples`` new sets of the same size, with replacement, take each one's median, and
    report the middle ``confidence`` of those medians. No distribution is assumed and none is
    fitted: the samples are the population.

    The interval answers one question — how much would this median move if the run were repeated
    under conditions like these — and it cannot answer any other. In particular a board that
    warms up during the run breaks the assumption that the samples are interchangeable, and the
    interval then looks tight while being wrong. That is not a flaw in the arithmetic. It is what
    the environment record beside it is for.
    """
    if not samples:
        raise ValueError("cannot bootstrap an empty sample set")
    if not 0 < confidence < 1:
        raise ValueError(f"confidence must be between 0 and 1, not {confidence}")
    if resamples < 1:
        raise ValueError("a bootstrap needs at least one resample")

    rng = random.Random(seed)
    population = list(samples)
    size = len(population)
    medians = sorted(statistics.median(rng.choices(population, k=size)) for _ in range(resamples))

    tail = (1.0 - confidence) / 2.0
    return (_at(medians, tail), _at(medians, 1.0 - tail))


def _at(ordered: Sequence[float], q: float) -> float:
    """Nearest-rank quantile, matching :func:`bench.measure._percentile`.

    Nearest-rank rather than interpolated for the same reason it is there: an interpolated bound
    reports a value no resample produced.
    """
    index = max(0, min(len(ordered) - 1, round(q * len(ordered) + 0.5) - 1))
    return ordered[index]


def bootstrap_difference_ci(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    resamples: int = RESAMPLES,
    seed: int = SEED,
    confidence: float = 0.90,
) -> tuple[float, float]:
    """An interval on ``median(candidate) - median(baseline)``.

    Both sides are resampled on each draw, because the question is about the difference and
    treating either side as exact would report an interval narrower than the evidence supports.
    Negative means the candidate is faster.
    """
    if not baseline or not candidate:
        raise ValueError("cannot compare an empty sample set")

    rng = random.Random(seed)
    left, right = list(baseline), list(candidate)
    differences = sorted(
        statistics.median(rng.choices(right, k=len(right)))
        - statistics.median(rng.choices(left, k=len(left)))
        for _ in range(resamples)
    )
    tail = (1.0 - confidence) / 2.0
    return (_at(differences, tail), _at(differences, 1.0 - tail))


# -- the decision ------------------------------------------------------------------------

#: What a comparison is allowed to conclude.
#:
#: "cannot tell" is a result, not a failure to get one. It is the answer whenever the evidence
#: does not separate the two, and a book that never printed it would be claiming a precision its
#: instrument does not have.
Verdict = Literal["faster", "slower", "cannot tell"]


def decide(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    threshold: float,
    resamples: int = RESAMPLES,
    seed: int = SEED,
    confidence: float = 0.90,
) -> dict[str, Any]:
    """Is the candidate faster than the baseline, by enough to matter?

    Two conditions, and both must hold:

    1. the bootstrap interval on the difference in medians excludes zero, so the run is evidence
       of a difference rather than of noise;
    2. the difference is at least ``threshold``, a fraction of the baseline median, stated before
       the measurement rather than after it.

    The second is the one people leave out, and leaving it out is how a run of ten thousand
    iterations comes to report a speedup nobody could observe. A threshold chosen afterwards is
    not a threshold; it is the result written twice.

    Returns the verdict and everything it was reached from, so a chapter can print the reasoning
    rather than the conclusion.
    """
    if threshold < 0:
        raise ValueError("a threshold is a size, so it cannot be negative")

    base_median = statistics.median(baseline)
    candidate_median = statistics.median(candidate)
    low, high = bootstrap_difference_ci(
        baseline, candidate, resamples=resamples, seed=seed, confidence=confidence
    )

    excludes_zero = low > 0 or high < 0
    difference = candidate_median - base_median
    relative = abs(difference) / base_median if base_median else 0.0
    big_enough = relative >= threshold

    if excludes_zero and big_enough:
        verdict: Verdict = "faster" if difference < 0 else "slower"
    else:
        verdict = "cannot tell"

    return {
        "verdict": verdict,
        "baseline_median": base_median,
        "candidate_median": candidate_median,
        "difference": difference,
        "relative": relative,
        "ci_difference": [low, high],
        "excludes_zero": excludes_zero,
        "threshold": threshold,
        "over_threshold": big_enough,
        "ci_method": "bootstrap",
        "resamples": resamples,
        "seed": seed,
        "confidence": confidence,
    }


def why(decision: dict[str, Any]) -> str:
    """One line saying which half of the rule settled it, for a chapter or a failing test."""
    if decision["verdict"] != "cannot tell":
        return (
            f"{decision['verdict']}: the interval {_interval(decision['ci_difference'])} excludes "
            f"zero and the difference is {decision['relative']:.1%} of the baseline, over the "
            f"{decision['threshold']:.1%} threshold"
        )
    if not decision["excludes_zero"]:
        return (
            f"cannot tell: the interval {_interval(decision['ci_difference'])} contains zero, so "
            "this run is consistent with there being no difference at all"
        )
    return (
        f"cannot tell: the interval {_interval(decision['ci_difference'])} excludes zero, but the "
        f"difference is {decision['relative']:.1%} of the baseline, under the "
        f"{decision['threshold']:.1%} threshold — real, and too small to care about"
    )


def _interval(bounds: Sequence[float]) -> str:
    return f"[{bounds[0]:.1f}, {bounds[1]:.1f}]"


# -- the environment ---------------------------------------------------------------------


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def environment() -> dict[str, Any]:
    """What the machine was doing, recorded beside the number it produced.

    Every field here moves a timing, and several move it further than any change to the code
    being timed. A result that does not carry them is a number without the conditions it was
    taken under, which is the thing this book refuses to print.

    Anything the machine declines to report comes back as ``None`` rather than a guess. A missing
    temperature is a fact about the board; a temperature invented for the sake of a complete
    record is a fact about nothing.
    """
    governor = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    frequency = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    temperature = _read("/sys/class/thermal/thermal_zone0/temp")

    try:
        pinned = sorted(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        pinned = None

    return {
        "governor": governor,
        "freq_khz": int(frequency) if frequency and frequency.isdigit() else None,
        # A set of allowed CPUs the size of the machine is not pinning, and saying so is the
        # point: an unpinned run may be measured on more than one core.
        "cpu_pinned": pinned if pinned is not None and len(pinned) == 1 else None,
        "cpus_allowed": pinned,
        "background_load": _load_average(),
        # millidegrees on every board that reports it at all
        "temp_c": round(int(temperature) / 1000.0, 1)
        if temperature and temperature.lstrip("-").isdigit()
        else None,
    }


def _load_average() -> float | None:
    try:
        return round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        return None


def describe_environment(record: dict[str, Any]) -> str:
    """The environment as one line, for a conditions note."""
    parts = [
        f"governor {record['governor']}" if record.get("governor") else "governor unknown",
        f"{record['freq_khz'] / 1000:.0f} MHz" if record.get("freq_khz") else "frequency unknown",
        f"pinned to CPU {record['cpu_pinned'][0]}" if record.get("cpu_pinned") else "not pinned",
        f"load {record['background_load']}"
        if record.get("background_load") is not None
        else "load unknown",
    ]
    if record.get("temp_c") is not None:
        parts.append(f"{record['temp_c']}°C")
    return ", ".join(parts)


# -- the stamp ---------------------------------------------------------------------------

#: Every field a distribution stamp must carry.
#:
#: Checked rather than documented, by `tests/test_book.py`, because a stamp missing one of these
#: is a figure the reader cannot judge — and the whole reason this block exists is that the book
#: used to print medians with nothing beside them.
REQUIRED_FIELDS: tuple[str, ...] = (
    "median",
    "p5",
    "p95",
    "ci_median",
    "ci_method",
    "resamples",
    "seed",
    "runs",
    "warmup_runs",
    "mode",
    "environment",
    "raw",
)

#: The environment fields a stamp has to have asked for. A `None` is an answer; an absent key is
#: a harness that never looked.
REQUIRED_ENVIRONMENT: tuple[str, ...] = (
    "governor",
    "freq_khz",
    "cpu_pinned",
    "background_load",
    "temp_c",
)


def distribution(
    samples: Sequence[float],
    *,
    warmup_runs: int,
    mode: Mode,
    raw: str,
    resamples: int = RESAMPLES,
    seed: int = SEED,
    confidence: float = 0.90,
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One timing, in the form Part V is allowed to print it.

    The median with a spread and an interval, the run count and mode that produced it, the
    environment it was taken in, and a path to every raw value so the whole thing can be
    re-analysed by somebody who does not trust this function.
    """
    if not samples:
        raise ValueError("cannot describe an empty sample set")
    ordered = sorted(samples)
    low, high = bootstrap_median_ci(ordered, resamples=resamples, seed=seed, confidence=confidence)
    return {
        "median": statistics.median(ordered),
        "p5": _at(ordered, 0.05),
        "p95": _at(ordered, 0.95),
        "min": ordered[0],
        "max": ordered[-1],
        "ci_median": [low, high],
        "ci_method": "bootstrap",
        "ci_confidence": confidence,
        "resamples": resamples,
        "seed": seed,
        "runs": len(ordered),
        "warmup_runs": warmup_runs,
        "mode": mode,
        "environment": env if env is not None else environment(),
        "raw": raw,
    }


def stamp_problems(block: dict[str, Any]) -> list[str]:
    """What is wrong with a distribution stamp, or nothing.

    Used by the guards and by the harness itself, so a result cannot be written in a shape the
    book would refuse to print.
    """
    problems = [f"missing {field}" for field in REQUIRED_FIELDS if field not in block]

    if "ci_median" in block:
        bounds = block["ci_median"]
        if not (isinstance(bounds, (list, tuple)) and len(bounds) == 2):
            problems.append("ci_median is not a pair")
        elif bounds[0] > bounds[1]:
            problems.append("ci_median is inverted")
        elif "median" in block and not bounds[0] <= block["median"] <= bounds[1]:
            problems.append("ci_median does not contain the median")

    if {"p5", "p95", "median"} <= set(block) and not block["p5"] <= block["median"] <= block["p95"]:
        problems.append("the median is outside p5..p95")

    if block.get("mode") not in (None, "cold", "warm") or "mode" not in block:
        problems.append(f"mode is {block.get('mode')!r}, which is neither 'cold' nor 'warm'")

    if isinstance(block.get("environment"), dict):
        problems += [
            f"environment never asked for {field}"
            for field in REQUIRED_ENVIRONMENT
            if field not in block["environment"]
        ]
    elif "environment" in block:
        problems.append("environment is not a record")

    return problems


def load_samples(path: Path | str) -> list[float]:
    """Read a raw values file: one sample per line, nanoseconds, nothing else."""
    text = Path(path).read_text()
    return [float(line) for line in text.split() if line]


def drop_page_cache() -> bool:
    """Ask the kernel to drop the page cache, for a cold run. True if it worked.

    Needs root, so it reports rather than raises: a cold run that silently became a warm one is
    the failure this is trying to make visible, and a harness that crashed on an unprivileged
    machine would just be run as warm instead.
    """
    try:
        subprocess.run(["sync"], check=True, capture_output=True)
        Path("/proc/sys/vm/drop_caches").write_text("3\n")
    except (OSError, subprocess.SubprocessError):
        return False
    return True
