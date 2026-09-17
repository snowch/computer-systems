#!/usr/bin/env python3
"""The virtual-memory chapter's measurement: what an address space costs to describe.

    python3 -m bench.run_pagetable           # boot, dump the page tables, stamp the shape
    python3 -m bench.run_pagetable --check   # re-run and compare; write nothing

Not a timing, and not because timing was inconvenient. A page table is consulted by hardware this
target does not model — QEMU has no TLB to miss and no memory to wait for — so the only honest
question here is a structural one: how many physical pages does the machine spend saying where
its other physical pages are? The memory-hierarchy chapter puts a price on a miss, on a machine
that can charge one.

Two rows, and both are structural constants rather than anything a run happened to produce. The
**kernel's** map is built once by ``kvmmake`` from a layout fixed at compile time. **init's** is
built by ``exec`` from a binary whose size is fixed by the linker, and init never calls ``sbrk``.
The shell's row is deliberately not recorded: xv6's shell mallocs while it parses, so its size is
a fact about what it has been asked to do rather than about address spaces. That distinction cost
the traps chapter a commit to learn.

The interesting part is the cross-check. ``sysfs/tools/sv39.c`` computes, from the runs of pages
alone and with no machine involved, how many page-table pages Sv39 requires to describe them. The
kernel counts its own tables by walking them. The two are arrived at from opposite ends and this
runner refuses to stamp a result in which they disagree — so the number in the chapter is not one
measurement but an agreement between a specification and a kernel.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from bench import xv6
from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.stamp import (
    ROOT,
    build_result,
    compiler_version,
    describe_qemu,
    load_result,
    measurement_differences,
    write_result,
)

MODEL = "sysfs/tools/sv39.c"
MODEL_LIB = "sysfs/lib/sv39.c"
PATCH = "xv6/patches/14-pagetable-census.patch"

#: Ctrl-V, which the patch binds to printing the census.
DUMP = "\x16"

#: The page tables recorded, keyed by the name the kernel prints. Both are decided by the build
#: rather than by the run; see the module docstring for why `sh` is not among them.
SUBJECTS = ("kernel", "init")


class CensusError(RuntimeError):
    """The kernel did not print a page-table census, or printed one that cannot be believed."""


def read_census(transcript: str) -> dict[str, Any]:
    """Turn the dump into one entry per page table, each with its runs of mapped pages."""
    tables: dict[str, Any] = {}
    regions: dict[str, list[dict[str, int]]] = {}
    complete = False

    for raw in transcript.splitlines():
        # The first census line shares a line with the shell prompt that was waiting when Ctrl-V
        # arrived, so the marker is found rather than assumed to start the line.
        if "end ptcensus" in raw:
            complete = True
            continue
        marker = raw.find("ptcensus ")
        if marker < 0:
            continue
        parts = raw[marker:].split()
        match parts[1:]:
            case ["region", kind, pid, start, pages]:
                regions.setdefault(f"{kind}:{pid}", []).append(
                    {"start": int(start, 16), "pages": int(pages)}
                )
            case [
                "table", kind, pid, name,
                "tables", t2, t1, t0,
                "leaves", f2, f1, f0,
                "bytes", mapped,
                "regions", count,
            ]:  # fmt: skip
                tables[name] = {
                    "table_pages": [int(t0), int(t1), int(t2)],
                    "leaf_entries": [int(f0), int(f1), int(f2)],
                    "bytes_mapped": int(mapped),
                    "regions": int(count),
                    "runs": regions.get(f"{kind}:{pid}", []),
                }

    if not complete or not tables:
        raise CensusError(f"no page-table census in the transcript:\n{transcript[-2000:]}")
    return tables


def parse_model(text: str) -> dict[str, Any]:
    """Read what the Sv39 model printed: its constants, and the tables a set of runs needs."""
    facts: dict[str, Any] = {"spans": {}}
    complete = False
    for raw in text.splitlines():
        parts = raw.split()
        match parts:
            case ["constant", name, value]:
                facts[name] = int(value)
            case ["span", level, value]:
                facts["spans"][level] = int(value)
            case ["tables", "l2", t2, "l1", t1, "l0", t0, "total", total]:
                facts["table_pages"] = [int(t0), int(t1), int(t2)]
                facts["total"] = int(total)
            case ["end", "sv39"]:
                complete = True
    if not complete:
        raise CensusError(f"the Sv39 model was cut off; got:\n{text}")
    return facts


def build_model(build_dir: Path) -> Path:
    """Build the Sv39 model for this machine. It is arithmetic; any machine will do."""
    native = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)
    built = compile_program(
        [MODEL, MODEL_LIB], build_dir / "sv39", native, includes=["sysfs/include"]
    )
    return built.path


def predict(model: Path, runs: list[dict[str, int]]) -> dict[str, Any]:
    arguments = [f"{run['start']:#x}:{run['pages']}" for run in runs]
    printed = subprocess.run(
        [str(model), "tables", *arguments], capture_output=True, text=True, check=True
    ).stdout
    return parse_model(printed)


def capture() -> dict[str, Any]:
    xv6.require()
    result = xv6.boot([DUMP])
    if result.timed_out:
        raise CensusError(f"xv6 did not print a census:\n{result.transcript[-2000:]}")
    census = read_census(result.transcript)

    build_dir = ROOT / "sysfs" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    model = build_model(build_dir)

    tables: dict[str, Any] = {}
    for name in SUBJECTS:
        if name not in census:
            raise CensusError(f"the census has no page table for {name!r}: {sorted(census)}")
        row = census[name]
        predicted = predict(model, row["runs"])
        if predicted["table_pages"] != row["table_pages"]:
            raise CensusError(
                f"the Sv39 model and the kernel disagree about {name}: the model derives "
                f"{predicted['table_pages']} page-table pages from the addresses, the kernel "
                f"counted {row['table_pages']} by walking them. One of the two is wrong and the "
                "book is not printing either until it is known which."
            )
        tables[name] = {**row, "table_pages_predicted": predicted["table_pages"]}

    # The runs are the explanation for every total above, but the kernel's are sixty-odd and most
    # of them are one page of kernel stack. Keep them where they explain something and summarise
    # them where they do not.
    tables["kernel"]["runs"] = _summarise(tables["kernel"]["runs"])

    sv39 = {key: value for key, value in parse_model(_constants(model)).items() if key != "total"}
    return build_result(
        name="pagetable-xv6",
        target="xv6",
        summary={"tables": tables, "sv39": sv39},
        code_sources=["bench/run_pagetable.py", "bench/xv6.py", MODEL, MODEL_LIB, PATCH],
        toolchain={
            "cc": compiler_version("riscv64-linux-gnu-gcc"),
            "flags": "xv6's own CFLAGS",
            "execution": "qemu-system-riscv64 -machine virt",
        },
        machine=describe_qemu(),
        conditions={
            "cpus": xv6.DEFAULT_CPUS,
            "note": "structure only: page-table pages, leaf entries and where the mappings are",
            "subjects": "the kernel's own map, and init's — both fixed by the build, not the run",
            "cross_check": "every table count is also derived from the addresses by sysfs/tools/sv39.c",
        },
    )


def _summarise(runs: list[dict[str, int]]) -> dict[str, Any]:
    """The kernel's runs, as the few facts about them a chapter can use."""
    pages = [run["pages"] for run in runs]
    return {
        "count": len(runs),
        "single_page": sum(1 for count in pages if count == 1),
        "largest_pages": max(pages, default=0),
        "first": runs[0] if runs else None,
    }


def _constants(model: Path) -> str:
    return subprocess.run(
        [str(model), "decode", "0x0"], capture_output=True, text=True, check=True
    ).stdout


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
        print(f"{payload['name']}: unchanged — these address spaces still have this shape")
        return 0
    print(f"{payload['name']}: the page tables have MOVED\n")
    for difference in differences:
        print(f"  {difference}")
    print(
        "\nRe-run and commit:\n  python3 -m bench.run_pagetable\n  python3 scripts/render-figures.py"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
