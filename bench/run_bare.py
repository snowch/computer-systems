"""Boot each of Part II's programs and record what it said.

    python3 -m bench.run_bare            # re-stamp every program
    python3 -m bench.run_bare --check    # fail if any of them stopped agreeing (CI)

A result here is a `measurement` on the ``bare`` target: the machine is QEMU, and the summary is
a set of counts and yes-or-no answers about what the processor did. It contains no duration and
may not — ``bench.stamp.provenance_problems`` refuses one, for the reason it refuses one from
``xv6``.

**Each program is refused unless it still demonstrates its chapter's claim.** A program that
boots, prints and exits cleanly is not evidence of anything on its own: ch04's trap could resume
without ever having been taken, ch06's harts could both run and lose nothing, ch09's fork could
return the same answer twice. The claims below are what each chapter actually says, written where
they will fail rather than in prose where they would simply become untrue.
"""

from __future__ import annotations

import argparse
import sys

from bench import bare
from bench.outline import CHAPTERS
from bench.stamp import (
    build_result,
    compiler_version,
    describe_bare,
    load_result,
    measurement_differences,
    write_result,
)

#: Which chapter each program belongs to. ch06 has two, because "what does translation do" and
#: "what does a second core break" are two questions and one program answering both would be
#: answering neither clearly.
CHAPTER_OF = {
    "trap": "a-trap-with-nothing-else",
    "privilege": "interrupts-and-privilege",
    "paging": "one-page-table-two-harts",
    "harts": "one-page-table-two-harts",
    "syscall": "a-system-call-of-your-own",
    "descriptors": "a-small-integer-that-means-a-device",
    "fork": "fork-built-rather-than-read",
}


def label_of(program: str) -> str:
    anchor = CHAPTER_OF[program]
    return next(c.label for c in CHAPTERS if c.anchor == anchor)


class ClaimFailedError(RuntimeError):
    """A program ran, and stopped showing what its chapter says it shows."""


#: program -> (harts, {field: expected}). ``None`` as an expectation means "must be true".
PROGRAMS: dict[str, tuple[int, dict[str, int | None]]] = {
    "trap": (
        1,
        {
            "mtvec_is_handler": None,
            "cause_is_ecall": None,
            "mepc_is_the_ecall": None,
            "register_survived": None,
            "resumed": None,
            "taken": 1,
        },
    ),
    "privilege": (
        1,
        {
            "interrupt_arrived": None,
            "cause_is_asynchronous": None,
            "interrupt_code": 7,
            "nothing_asked_for_it": None,
            "machine_register_refused": None,
            "refusal_is_illegal_instruction": None,
            "back_in_machine_mode": None,
        },
    ),
    "paging": (
        1,
        {
            "entries_used": 3,
            "reached_supervisor": None,
            "alias_reads_the_same": None,
            "machine_mode_ignores_satp": None,
            "unexpected_cause": 0,
        },
    ),
    "harts": (
        2,
        {
            "second_hart_ran": None,
            "counter_after": 1,
            # The whole demonstration. If the two halves of the read-modify-write stopped being
            # held apart, this would read 0 and the chapter would be claiming something it had
            # stopped showing.
            "updates_lost": 1,
            "atomic_counter_after": 2,
            "atomic_updates_lost": 0,
        },
    ),
    "syscall": (
        1,
        {
            "registers_in_frame": 31,
            "number_crossed": None,
            "arguments_crossed": None,
            "result_returned": 7,
            "caller_register_in_frame": None,
            "caller_register_intact": None,
            "unknown_call_refused": 1,
            "unknown_returned_error": None,
        },
    ),
    "descriptors": (
        1,
        {
            "same_call_reached_both": None,
            "cursor_after_writing": 6,
            # The chapter's central surprise. If a read after a write ever returned bytes without
            # the cursor being moved first, the cursor would have stopped being a position and
            # the chapter would be describing something else.
            "read_without_rewinding": 0,
            "read_after_rewinding": 6,
            "memory_kept_the_bytes": None,
            "closed_slot_refused": None,
            "dup_returned": 3,
            "dup_shares_the_open_file": None,
            # Two descriptors, one open file, one position: the byte written through the
            # duplicate lands after what was already there rather than on top of it.
            "cursor_after_dup_write": 7,
            "dup_appended_rather_than_overwrote": None,
            "read_everything": 7,
            "unexpected_trap": 0,
        },
    ),
    "fork": (
        1,
        {
            "processes": 2,
            "pages_copied": 1,
            "parent_result": 1,
            "child_result": 0,
            "results_differ": None,
            "both_ran": None,
            "child_saw_the_parents_byte": None,
            "childs_write_stayed_in_its_own_page": None,
            "unexpected_trap": 0,
        },
    ),
}


def check_claims(program: str, fields: dict[str, int]) -> None:
    expected = PROGRAMS[program][1]
    broken = []
    for field, want in expected.items():
        if field not in fields:
            broken.append(f"{field} was not printed at all")
        elif want is None and not fields[field]:
            broken.append(f"{field} is false")
        elif want is not None and fields[field] != want:
            broken.append(f"{field} is {fields[field]}, expected {want}")
    if broken:
        raise ClaimFailedError(
            f"{program} booted and stopped showing what its chapter says it shows:\n  "
            + "\n  ".join(broken)
        )


def measure(program: str) -> dict:
    harts, _ = PROGRAMS[program]
    run = bare.run(program, harts=harts)
    fields = run.fields()
    check_claims(program, fields)
    return build_result(
        name=f"{program}-bare",
        target="bare",
        kind="measurement",
        summary={"program": program, "harts": harts, **fields},
        code_sources=list(bare.sources_for(program)),
        toolchain={
            "cc": bare.CC,
            "cc_version": compiler_version(bare.CC),
            "flags": list(bare.CFLAGS),
        },
        machine=describe_bare(),
        conditions={
            "harts": harts,
            "note": "counts and yes-or-no answers only; nothing on this target may be timed",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare, do not write")
    parser.add_argument("program", nargs="?", help="just this one")
    args = parser.parse_args()

    if found := bare.problems():
        print(f"bare: SKIPPED — {'; '.join(found)}")
        return 0

    wanted = [args.program] if args.program else list(PROGRAMS)
    stale = []
    for program in wanted:
        fresh = measure(program)
        if not args.check:
            write_result(fresh)
            print(f"wrote bench/results/{fresh['name']}.json")
            continue
        committed = load_result(fresh["name"])
        differences = measurement_differences(committed, fresh)
        if differences:
            stale.append(f"{fresh['name']}: {'; '.join(differences)}")
        else:
            print(
                f"{fresh['name']}: unchanged — the machine still does what {label_of(program)} says"
            )

    if stale:
        print("bare: FAILED")
        for line in stale:
            print(f"  - {line}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
