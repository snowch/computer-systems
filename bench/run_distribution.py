"""The measurement chapter's second half: how wrong a number is, measured on the board.

Four experiments, one workload, and every one of them keeps its samples:

* **the harness** — an empty measured region, timed the same way as a real one, so the chapter
  can say what the instrument costs and show that the cost has a spread of its own;
* **warm against cold** — the same work with the caches left alone and with them evicted, which
  the chapter argues are two experiments rather than one experiment with noise in it;
* **the interval against the run count** — the same samples, analysed at several counts, showing
  where a bootstrap interval stops narrowing;
* **plain against unrolled** — two variants of one loop, put to the decision rule with a
  threshold fixed before the run.

Unlike `run_measuring.py`, which summarises in C and keeps nothing, every run here writes its
samples to `bench/raw/` and the stamp records the path. That is the whole point: an interval is
computed from samples, so a result that discarded them could only ever be re-measured, and
re-measuring needs the board.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bench.board import governor, require_board, stamp_timing, timed_run
from bench.distribution import (
    RESAMPLES,
    SEED,
    bootstrap_median_ci,
    decide,
    describe_environment,
    distribution,
    drop_page_cache,
    environment,
    load_samples,
)
from bench.stamp import ROOT, write_result

FIGURE = "measuring-harness, measuring-temperature, measuring-runs and measuring-verdict"

WORKLOAD = "sysfs/bench/distcost.c"
HARNESS = "sysfs/lib/distribution.c"

#: Where raw samples live. Committed alongside the result, because a stamp that names a file
#: nobody can read is a citation of something that does not exist.
RAW = ROOT / "bench" / "raw"

#: Runs per experiment, and the warm-up discarded before them.
#:
#: Chosen from the run-count experiment below rather than by habit: the interval stops narrowing
#: well before this, so more would buy nothing and the chapter would be recommending what it does
#: not do.
RUNS = 400
WARMUP = 50

#: Stated before the measurement, which is the only time a threshold means anything. Two per cent
#: is roughly where this book stops caring: a change smaller than that is invisible in anything
#: the reader will build on top of it.
THRESHOLD = 0.02

#: The run counts the interval is recomputed at, to show it narrowing and then stopping.
COUNTS = (10, 25, 50, 100, 200, 400)


#: The summary this runner writes, so `tests/test_board.py` can check today — with no board in the
#: room — that what this writes is what `bench/tables.py` reads. A runner and a renderer that
#: disagree about a key are two files that each look correct, and the disagreement surfaces on the
#: one afternoon the hardware is plugged in.
#:
#: 111 and 222 throughout, so that one of them reaching a rendered page would be unmistakable.
def _block(mode: str = "warm") -> dict[str, Any]:
    return {
        "median": 222,
        "p5": 111,
        "p95": 222,
        "min": 111,
        "max": 222,
        "ci_median": [111, 222],
        "ci_method": "bootstrap",
        "ci_confidence": 0.9,
        "resamples": 222,
        "seed": 111,
        "runs": 222,
        "warmup_runs": 111,
        "mode": mode,
        "environment": {
            "governor": "shape",
            "freq_khz": 111,
            "cpu_pinned": [1],
            "cpus_allowed": [1],
            "background_load": 1.11,
            "temp_c": 22.2,
        },
        "raw": "bench/raw/shape.txt",
    }


SHAPE = {
    "harness": _block(),
    "plain": _block(),
    "unrolled": _block(),
    "cold": _block("cold"),
    "narrowing": [{"runs": 111, "ci_median": [111, 222], "width": 111}],
    "verdict": {
        "verdict": "cannot tell",
        "baseline_median": 222,
        "candidate_median": 222,
        "difference": 111,
        "relative": 0.111,
        "ci_difference": [111, 222],
        "excludes_zero": True,
        "threshold": 0.02,
        "over_threshold": False,
        "ci_method": "bootstrap",
        "resamples": 222,
        "seed": 111,
        "confidence": 0.9,
    },
    "governor": "shape",
}


def run_variant(variant: str, mode: str, runs: int = RUNS) -> list[float]:
    """One experiment, keeping every sample."""
    RAW.mkdir(parents=True, exist_ok=True)
    raw = RAW / f"distcost-{variant}-{mode}.txt"
    if mode == "cold":
        drop_page_cache()
    timed_run(
        [WORKLOAD, HARNESS],
        "distcost",
        [
            "--warmup",
            str(WARMUP),
            "--runs",
            str(runs),
            "--mode",
            mode,
            "--raw",
            str(raw),
            "--which",
            variant,
        ],
    )
    return load_samples(raw)


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def measure() -> dict[str, Any]:
    env = environment()

    plain = run_variant("plain", "warm")
    unrolled = run_variant("unrolled", "warm")
    empty = run_variant("nothing", "warm")
    cold = run_variant("plain", "cold")

    def block(samples: list[float], variant: str, mode: str) -> dict[str, Any]:
        return distribution(
            samples,
            warmup_runs=WARMUP,
            mode=mode,
            raw=relative(RAW / f"distcost-{variant}-{mode}.txt"),
            env=env,
        )

    # How the interval behaves as the count grows. Prefixes of one run rather than separate runs,
    # so the only thing changing is how much of the evidence is being used.
    narrowing = []
    for count in COUNTS:
        low, high = bootstrap_median_ci(plain[:count])
        narrowing.append({"runs": count, "ci_median": [low, high], "width": high - low})

    verdict = decide(plain, unrolled, threshold=THRESHOLD)

    return {
        "harness": block(empty, "nothing", "warm"),
        "plain": block(plain, "plain", "warm"),
        "unrolled": block(unrolled, "unrolled", "warm"),
        "cold": block(cold, "plain", "cold"),
        "narrowing": narrowing,
        "verdict": verdict,
        "governor": governor(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare, do not write")
    args = parser.parse_args()

    require_board("the measurement chapter's distribution figures")
    summary = measure()

    # The one thing this runner refuses. If the workload is not many times the harness, the
    # figure would be mostly instrument, and the chapter's own rule says not to publish it.
    ratio = summary["plain"]["median"] / summary["harness"]["median"]
    if ratio < 100:
        raise SystemExit(
            f"the workload is only {ratio:.0f}x the harness. The chapter's own rule is that a "
            "measured region must be many times the instrument, so this would be a figure about "
            "the clock. Raise ROUNDS in the workload and re-run."
        )

    payload = stamp_timing(
        "distribution-host",
        summary,
        [WORKLOAD, HARNESS, "sysfs/include/sysfs/distribution.h", "bench/distribution.py"],
        note=(
            f"{RUNS} runs after {WARMUP} discarded, bootstrap of {RESAMPLES} resamples at "
            f"seed {SEED}; {describe_environment(summary['plain']['environment'])}"
        ),
        workload=WORKLOAD,
    )

    if args.check:
        print(json.dumps(payload["summary"], indent=2, default=str))
        return 0

    write_result(payload)
    print(f"wrote bench/results/distribution-host.json and {len(COUNTS)} interval widths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
