#!/usr/bin/env python3
"""Chapter 20's census: what the program under the profiler is about to do, counted.

    python3 -m bench.run_profile           # run the census and stamp it
    python3 -m bench.run_profile --check   # re-run and compare; write nothing

The chapter hands the reader a program and asks where the time goes. This runner records the
program's *shape* first — records, table width, how much of the table each arrangement touches at
once, how lopsided the conditional in the phase that looks expensive is — and every one of those
is a property of the program and its sizes rather than of any machine, so CI regenerates it.

Recording it is the chapter's method rather than its decoration. A profile with nothing written
down beforehand is very easy to agree with: whatever it blames becomes what you expected. The
census is a prediction committed to before the measurement exists, and ch22 is about what
happens when the two disagree.

Three refusals, because a census that quietly stopped describing the program would be worse than
no census at all. The two arrangements must compute the same checksum, or the comparison in the
chapter is between two different programs. The scattered pass must still reach every cache line of
the table, or the workload has stopped being scattered and the chapter demonstrates nothing. And
the conditional must stay lopsided, or the phase that is supposed to look expensive and be cheap
has become genuinely expensive, and the chapter's argument inverts without anybody noticing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from bench.measure import compile_program, resolve_host_target
from bench.stamp import (
    ROOT,
    build_result,
    describe_counted_run,
    load_result,
    measurement_differences,
    write_result,
)

PROGRAM = "sysfs/tools/tally.c"
LIBRARY = "sysfs/lib/profiling.c"
HEADER = "sysfs/include/sysfs/profiling.h"

#: The conditional in the decode phase is there to be seen in the source and found innocent. Below
#: this it is not innocent any more, and the chapter would be pointing at the wrong thing.
LOPSIDED = 0.99


class CensusError(RuntimeError):
    """The program stopped being the program the chapter describes."""


def parse(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    complete = False
    for line in text.splitlines():
        parts = line.split()
        match parts:
            case ["tally", "records", records, "entries", entries, "line_bytes", line_bytes]:
                facts |= {
                    "records": int(records),
                    "entries": int(entries),
                    "line_bytes": int(line_bytes),
                }
            case ["tally", "table_bytes", table_bytes, "slice_bytes", slice_bytes]:
                facts |= {"table_bytes": int(table_bytes), "slice_bytes": int(slice_bytes)}
            case ["tally", "decode", "taken", taken, "of", _]:
                facts["decode_taken"] = int(taken)
            case ["tally", "scatter", "distinct_keys", distinct, "lines", lines]:
                facts |= {"distinct_keys": int(distinct), "lines_touched": int(lines)}
            case [
                "tally", "partitioned",
                "buckets", buckets,
                "slice_entries", slice_entries,
                "key_reads", key_reads,
                "key_writes", key_writes,
            ]:  # fmt: skip
                facts |= {
                    "buckets": int(buckets),
                    "slice_entries": int(slice_entries),
                    "key_reads": int(key_reads),
                    "key_writes": int(key_writes),
                }
            case ["tally", "checksum", "scatter", scatter, "partitioned", part, "agree", agree]:
                facts |= {
                    "checksum": int(scatter),
                    "checksum_partitioned": int(part),
                    "agree": agree == "yes",
                }
            case ["end", "tally"]:
                complete = True
    if not complete:
        raise CensusError(f"tally did not finish; it printed:\n{text}")
    return facts


def refuse_a_census_that_no_longer_describes_the_chapter(facts: dict[str, Any]) -> None:
    if not facts["agree"]:
        raise CensusError(
            "the two arrangements computed different checksums "
            f"({facts['checksum']} and {facts['checksum_partitioned']}). They are supposed to be "
            "the same program written twice; ch22 compares their profiles, and a comparison "
            "between two different answers is not one."
        )

    lines_in_table = facts["table_bytes"] // facts["line_bytes"]
    if facts["lines_touched"] != lines_in_table:
        raise CensusError(
            f"the scattered pass reached {facts['lines_touched']} of the table's "
            f"{lines_in_table} cache lines. It is supposed to reach all of them — that is what "
            "makes it scattered, and what the chapter's first profile is about."
        )

    lopsided = facts["decode_taken"] / facts["records"]
    if lopsided < LOPSIDED:
        raise CensusError(
            f"the decode phase's conditional is taken {lopsided:.4f} of the time, below "
            f"{LOPSIDED}. It exists to look expensive in the source and be cheap in the "
            "measurement; a conditional this close to even is genuinely expensive, and the "
            "chapter would be pointing at the wrong phase."
        )


def capture() -> dict[str, Any]:
    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    target = resolve_host_target()
    built = compile_program(
        [PROGRAM, LIBRARY], build_dir / "tally", target, includes=["sysfs/include"]
    )
    facts = parse(built.run(["census"]).stdout)
    refuse_a_census_that_no_longer_describes_the_chapter(facts)

    return build_result(
        name="tally-census",
        target="host",
        kind="artefact",
        summary=facts | {"built_for": target.name},
        code_sources=["bench/run_profile.py", PROGRAM, LIBRARY, HEADER],
        toolchain={
            "cc": target.cc,
            "flags": " ".join(target.flags),
            "execution": "run for its counts; user-mode QEMU is enough for those and never for a "
            "duration",
        },
        machine=describe_counted_run("aarch64"),
        conditions={
            "note": "counts only — every figure here is a property of the program and its sizes",
            "why": "the profile itself belongs to make bench-board, and this is what it is "
            "compared against",
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
        print(f"{payload['name']}: unchanged — the program still has the shape ch22 describes")
        return 0
    print(f"{payload['name']}: the program has MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_profile\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
