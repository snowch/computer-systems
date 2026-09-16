"""Turning committed results into the markdown the chapters include.

Imports nothing but the standard library, on purpose: this runs in CI on every push, and a table
renderer that needs a scientific Python stack installed is a table renderer that breaks for
reasons having nothing to do with the book.

The rule these functions exist to enforce is that **no number is ever typed into prose**
(PLAN.md §6.3). If a figure appears in this book it came from a file under ``bench/results/``
that names the target, the machine, the kernel, the compiler and the flags that produced it.
"""

from __future__ import annotations

import re
from typing import Any

from bench.outline import CHAPTERS
from bench.stamp import load_result

#: A chapter's displayed number comes from the outline, never from a stamped result: the
#: result records which chapter reads a file, and where that chapter currently sits is not
#: a fact about the kernel tree.
_by_anchor = {chapter.anchor: chapter for chapter in CHAPTERS}


def _cell(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    """A GitHub-flavoured markdown table. Alignment is the theme's business, not ours."""
    lines = ["| " + " | ".join(headers) + " |", "|---" * len(headers) + "|"]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def conditions(name: str) -> str:
    """The provenance line under a table: where this number came from, in one sentence.

    Every table in the book carries one. A measurement without its conditions is an anecdote, and
    the conditions are precisely what a reader needs in order to disagree with it.
    """
    result = load_result(name)
    machine = result.get("machine", {})
    toolchain = result.get("toolchain", {})
    parts = [f"target `{result['target']}`"]

    model = machine.get("model")
    if model:
        parts.append(model)
    if machine.get("emulator"):
        parts.append(machine["emulator"])
    if machine.get("kernel"):
        parts.append(machine["kernel"])
    if toolchain.get("cc"):
        parts.append(toolchain["cc"])
    flags = toolchain.get("flags")
    if flags:
        # A runner that hands over a list rather than a command line would otherwise put Python's
        # own repr on the page, brackets and quotes and all, which is four lines of noise on a
        # phone. It happened.
        if not isinstance(flags, str):
            flags = " ".join(str(flag) for flag in flags)
        parts.append(f"`{flags}`")
    parts.append(result["generated_at"][:10])
    parts.append(f"Source: `bench/results/{name}.json`, code hash `{result['code_fingerprint']}`")
    # Middots rather than semicolons: these are heterogeneous facts rather than a sentence, and a
    # reader looking for one of them is scanning rather than reading.
    return "*Conditions: " + " · ".join(parts) + ".*"


def listing(name: str, symbol: str) -> str:
    """One function's disassembly, fenced, from a committed ``kind: listing`` result.

    The fence is tagged ``asm`` so the site highlights it; the PDF renderer takes the language
    from the same place. Nothing else is done to the text. What objdump printed is what the reader
    sees, which is the only version of this that survives them running the command themselves.
    """
    result = load_result(name)
    if result.get("kind") != "listing":
        raise ValueError(f"{name} is a {result.get('kind')!r} result, not a listing")
    listings = result["summary"]["listings"]
    if symbol not in listings:
        raise KeyError(
            f"{name} has no listing for {symbol!r}; it has "
            f"{', '.join(sorted(listings)) or 'none'}. Add it to SYMBOLS in bench/run_disasm.py."
        )
    return "```asm\n" + listings[symbol]["text"] + "\n```"


def listing_instructions(name: str, symbol: str) -> int:
    """How many instructions that listing contains, for prose that counts them."""
    return load_result(name)["summary"]["listings"][symbol]["instructions"]


_OPTIMISATION_FLAG = re.compile(r"-O\w+|-f[\w-]+")


def optimisation_level(result: dict[str, Any]) -> str:
    """The flags a listing was built with that decide what the compiler is allowed to emit.

    The last ``-O`` wins, because that is what a command line does and because ch28 builds the
    same source at two levels by appending one to the other exactly as a reader would. Any ``-f``
    flags come with it, and they have to: two of ch28's three builds are both ``-O3`` and differ
    only in whether the compiler may change the program's answer, so a label naming the level
    alone would put two different listings under identical headings.
    """
    found = _OPTIMISATION_FLAG.findall(result.get("toolchain", {}).get("flags", ""))
    levels = [flag for flag in found if flag.startswith("-O")]
    return " ".join(([levels[-1]] if levels else []) + [f for f in found if f[1] != "O"])


def listing_label(name: str, symbol: str) -> str:
    """The line above a listing: what it is, which architecture and level, and how long it is.

    Assembled from the result rather than typed, like everything else here. The instruction count
    in particular: it is the figure a chapter comparing two architectures most wants to quote, and
    a hand-typed one would be the first thing to go stale.

    The optimisation level is in the label rather than only in the conditions line underneath
    because ch28 prints the same function twice, from two levels, and without it the two blocks
    are indistinguishable at a glance — which is the one thing the figure is for.
    """
    result = load_result(name)
    arch = result["machine"]["arch"]
    level = optimisation_level(result)
    count = listing_instructions(name, symbol)
    at = f" at `{level}`" if level else ""
    return (
        f"**`{symbol}` compiled for {arch}{at}** — the `{result['target']}` target's instruction "
        f"set, {count} instructions."
    )


# -- the renderers chapters ask for -------------------------------------------------------


def probe_types_table(name: str) -> str:
    """What one target says the C scalar types are.

    Sizes and alignments only. There is nothing here about speed, which is the point: this is the
    kind of question the xv6 target answers perfectly well.
    """
    summary = load_result(name)["summary"]
    rows = [
        [f"`{fact['name'].replace('_', ' ')}`", fact["size"], fact["align"]]
        for fact in summary["types"]
    ]
    return render_table(["C type", "Bytes", "Alignment"], rows)


def probe_layout_table(name: str) -> str:
    """Two structs with the same members in different orders, and what that costs."""
    summary = load_result(name)["summary"]
    rows = [
        [
            f"`{fact['name']}`",
            fact["size"],
            fact["align"],
            fact["padding"],
        ]
        for fact in summary["layouts"]
    ]
    return render_table(
        ["Struct", "`sizeof`", "Alignment", "Bytes that hold nothing"],
        rows,
    )


def stage_sizes_table(name: str) -> str:
    """What each stage produced, in bytes and lines.

    Both columns, because they disagree in a way worth noticing: the assembler's output is larger
    in bytes than the compiler's and far smaller in lines, which is what it looks like when text
    becomes a container format.
    """
    summary = load_result(name)["summary"]
    rows = [[f"`{stage['stage']}`", stage["bytes"], stage["lines"]] for stage in summary["stages"]]
    return render_table(["Stage", "Bytes it produced", "Lines"], rows)


def linking_cost_table(name: str) -> str:
    """The same program, linked two ways, and what the object still owed the linker."""
    summary = load_result(name)["summary"]
    rows = [
        ["Object file, before linking", summary["stages"][2]["bytes"]],
        ["Symbols the object left undefined", summary["undefined_in_object"]],
        ["Linked against glibc, statically", summary["linux_program_bytes"]],
        ["Linked by xv6, against its own user library", summary["xv6_program_bytes"]],
        ["Symbols the program leaves undefined", summary["undefined_in_program"]],
    ]
    return render_table(["What", "Count"], rows)


def frame_sizes_table(name: str) -> str:
    """Frame size and instruction mix for each function, at both optimisation levels.

    One row per function with the two levels side by side, because the comparison is the content:
    reading down a column says what an optimiser does to memory traffic far more directly than
    two separate tables would.
    """
    rows_by_symbol: dict[str, dict[str, dict]] = {}
    for row in load_result(name)["summary"]["functions"]:
        rows_by_symbol.setdefault(row["symbol"], {})[row["level"]] = row

    rows = []
    for symbol, levels in rows_by_symbol.items():
        low, high = levels["-O0"], levels["-O2"]
        rows.append(
            [
                f"`{symbol}`",
                low["frame_bytes"],
                high["frame_bytes"],
                low["instructions"],
                high["instructions"],
                low["load"] + low["store"],
                high["load"] + high["store"],
            ]
        )
    return render_table(
        [
            "Function",
            "Frame `-O0`",
            "Frame `-O2`",
            "Instructions `-O0`",
            "Instructions `-O2`",
            "Memory ops `-O0`",
            "Memory ops `-O2`",
        ],
        rows,
    )


def elf_segments_table(name: str) -> str:
    """What the loader is told to do, per program: where, how much, and how much more."""
    programs = load_result(name)["summary"]["programs"]
    rows = []
    for program, facts in sorted(programs.items()):
        for segment in facts["segments"]:
            permissions = "".join(
                letter if segment["flags"] & bit else "-"
                for bit, letter in ((4, "r"), (2, "w"), (1, "x"))
            )
            rows.append(
                [
                    f"`{program}`",
                    permissions,
                    segment["vaddr"],
                    segment["file_bytes"],
                    segment["memory_bytes"],
                    segment["memory_bytes"] - segment["file_bytes"],
                ]
            )
    return render_table(
        ["Program", "Permissions", "Loaded at", "Bytes in the file", "Bytes in memory", "Zeroed"],
        rows,
    )


def elf_shape_table(name: str) -> str:
    """How many of each thing, per program. The collapse from sections to segments is the row."""
    programs = load_result(name)["summary"]["programs"]
    rows = [
        [
            f"`{program}`",
            len(facts["sections"]),
            len(facts["segments"]),
            facts["defined_symbols"],
            facts["undefined_symbols"],
        ]
        for program, facts in sorted(programs.items())
    ]
    return render_table(
        ["Program", "Sections", "Loadable segments", "Symbols defined", "Symbols undefined"], rows
    )


def trap_path_table(name: str) -> str:
    """The two halves of the trap path, counted."""
    path = load_result(name)["summary"]["path"]
    rows = [
        [
            f"`{half}`",
            facts["instructions"],
            facts["register_stores"],
            facts["register_loads"],
            facts["csr_operations"],
        ]
        for half, facts in sorted(path.items())
    ]
    return render_table(
        ["Half of the path", "Instructions", "Registers saved", "Registers restored", "CSR ops"],
        rows,
    )


def trap_census_table(name: str) -> str:
    """What the kernel was entered for, recording only what the workload decided."""
    census = load_result(name)["summary"]["census"]
    causes = {
        2: "illegal instruction",
        8: "system call (`ecall` from user mode)",
        12: "instruction page fault",
        13: "load page fault",
        15: "store page fault",
    }
    rows = [
        [
            f"`getpid` calls the workload asked for (syscall {census['probe_syscall']})",
            census["probe_calls_counted"],
        ],
        [
            "Exception causes seen",
            ", ".join(causes.get(c, str(c)) for c in census["exception_causes_seen"]),
        ],
        [
            "Interrupt causes seen (counts deliberately not recorded)",
            ", ".join(str(c) for c in census["interrupt_causes_seen"]),
        ],
    ]
    return render_table(["What the kernel was entered for", "This run"], rows)


def xv6_environment_table(name: str) -> str:
    """What booting the teaching kernel actually produced, as facts rather than as a claim."""
    result = load_result(name)
    summary = result["summary"]
    machine = result["machine"]
    rows = [
        ["Kernel", machine["kernel"]],
        ["Emulator", machine["emulator"]],
        ["Machine model", machine["model"]],
        ["Harts started", summary["harts"]],
        ["User programs in the image", summary["user_programs"]],
        ["Kernel image size (bytes)", summary["kernel_bytes"]],
        ["Byte order", summary["endian"]],
    ]
    return render_table(["What", "This boot"], rows)


#: ``/proc/cpuinfo`` key -> the label this table gives it, in the order the rows appear.
#:
#: Both architectures are listed because the reference machine is an ARM one and a reader
#: following Part V on a RISC-V board is supported. A key absent from this mapping is still
#: printed, under its own name: a table that silently dropped something the kernel reported would
#: be a table you could not trust to be complete, which is the opposite of what it is for.
CORE_IDENTITY_LABELS = {
    # RISC-V
    "isa": "ISA string",
    "uarch": "Microarchitecture",
    "mmu": "MMU",
    "mvendorid": "`mvendorid`",
    "marchid": "`marchid`",
    "mimpid": "`mimpid`",
    # ARM
    "cpu implementer": "CPU implementer",
    "cpu architecture": "CPU architecture",
    "cpu variant": "CPU variant",
    "cpu part": "CPU part",
    "cpu revision": "CPU revision",
    "features": "Features",
    # anywhere
    "model name": "Model name",
}

#: Reported by the kernel, and not a measurement of anything: a calibration loop whose result
#: depends on the kernel's own timing code. Skipped by name rather than quietly, so that the
#: decision is visible to anyone wondering where it went.
CORE_IDENTITY_SKIP = ("bogomips",)


def core_identity_rows(cpu: dict[str, Any]) -> list[list[Any]]:
    """What the running kernel says this core is, whichever architecture it is."""
    known = [
        [label, cpu[key]] for key, label in CORE_IDENTITY_LABELS.items() if cpu.get(key) is not None
    ]
    extra = [
        [key, value]
        for key, value in sorted(cpu.items())
        if key not in CORE_IDENTITY_LABELS and key not in CORE_IDENTITY_SKIP
    ]
    return known + extra


def board_identity_table(name: str) -> str:
    """The board's account of itself, read from the running machine rather than a datasheet.

    A spec sheet describes a product line. ``/proc/cpuinfo`` describes the silicon that produced
    the numbers in every other table in Part V, which is the one that matters when two of them
    disagree.

    Nothing here is architecture-specific, deliberately. The reference machine is an ARM one and a
    RISC-V board reports an entirely different set of fields; a table hard-coded to either would
    print a column of dashes on the other and look like a broken measurement rather than a
    different machine.
    """
    result = load_result(name)
    summary = result["summary"]
    machine = result["machine"]
    rows: list[list[Any]] = [
        ["Board (device tree)", machine.get("model")],
        # Image and kernel together, because the counters are a property of the configuration and
        # not only of the silicon: the reference board's own PMU went missing for a kernel
        # release. ch00 tells the reader to verify rather than match this row.
        ["Operating system", machine.get("os")],
        ["Kernel", machine.get("kernel")],
        ["Cores online", machine.get("cpus_online")],
        ["Native compiler", result.get("toolchain", {}).get("cc")],
    ]
    rows += core_identity_rows(machine.get("cpu", {}))
    rows += [
        # The two capabilities Part V is built on, and they are separate questions: a core can
        # count perfectly well and be unable to sample at all. ch00 says why.
        ["`perf stat` reads hardware counters", summary.get("perf_counters_readable")],
        ["Cycle counter event", summary.get("perf_cycles_event")],
        ["`perf record` can sample", summary.get("perf_can_sample")],
        ["Samples collected in the capability check", summary.get("perf_samples")],
    ]
    return render_table(["What", "This board"], rows)


def pagetable_shape_table(name: str) -> str:
    """What each address space maps, and what describing it costs.

    Two rows and one comparison. The kernel's map is enormous and nearly free per byte; init's is
    tiny and mostly overhead. Reading across explains why: the cost follows the number of separate
    regions, and neither the number of pages nor the number of bytes predicts it.
    """
    tables = load_result(name)["summary"]["tables"]
    rows = []
    for label in ("kernel", "init"):
        entry = tables[label]
        table_pages = sum(entry["table_pages"])
        mapped = entry["leaf_entries"][0]
        rows.append(
            [
                f"`{label}`",
                table_pages,
                mapped,
                entry["regions"],
                f"{100 * table_pages / mapped:.3g}%",
            ]
        )
    return render_table(
        ["Address space", "Page-table pages", "Pages mapped", "Separate regions", "Overhead"], rows
    )


def sv39_geometry_table(name: str) -> str:
    """Sv39's shape, and the two numbers the whole of it follows from.

    Printed rather than asserted because the chapter's claim is that none of this is arbitrary:
    given a page size and an entry size, every other figure in the table is forced.
    """
    sv39 = load_result(name)["summary"]["sv39"]
    rows = [
        ["Page size", f"{sv39['page_bytes']} bytes", "chosen"],
        ["Page-table entry", f"{sv39['entry_bytes']} bytes", "chosen"],
        ["Entries per table", sv39["entries_per_table"], "page ÷ entry"],
        ["Index bits per level", sv39["index_bits"], "log₂(entries)"],
        ["Levels", sv39["levels"], "to reach 39 bits"],
        ["One level-0 entry covers", f"{sv39['spans']['0']} bytes", "a page"],
        ["One level-1 entry covers", f"{sv39['spans']['1']} bytes", "512 pages"],
        ["One level-2 entry covers", f"{sv39['spans']['2']} bytes", "512 of those"],
    ]
    return render_table(["", "Value", "Where it comes from"], rows)


def fault_exchange_table(name: str) -> str:
    """What laziness saved, and what it cost to save it.

    Both columns of the trade in one place, because quoting either alone is how the feature gets
    described as free. Pages are what a policy saves; faults are what it spends.
    """
    run = load_result(name)["summary"]["faultload"]
    rows = [
        ["Pages requested with `sbrklazy`", run["asked_lazy"]],
        ["…of those, pages ever touched", run["touched_lazy"]],
        ["…so pages never allocated at all", run["pages_never_allocated"]],
        ["Entries into the kernel that cost", run["load_faults"] + run["store_faults"]],
        ["Pages requested with `sbrk`", run["asked_eager"]],
        ["…of those, pages allocated", run["asked_eager"]],
        ["Pages `exec` allocated before `main` ran", run["eager_pages_before_main"]],
    ]
    return render_table(["What the workload did", "Pages"], rows)


def fault_causes_table(name: str) -> str:
    """Which fault each page arrived on, and how many the kernel declined.

    The hardware reports a load fault and a store fault as different causes. Whether a kernel uses
    the distinction is a separate question, and this table is how you find out what this one does.
    """
    run = load_result(name)["summary"]["faultload"]
    rows = [
        ["Load page fault", "13", run["load_faults"]],
        ["Store page fault", "15", run["store_faults"]],
        ["Faults the handler declined", "—", run["refused"]],
    ]
    return render_table(["Cause", "`scause`", "Count"], rows)


def interrupt_cost_table(name: str) -> str:
    """What a fixed amount of I/O cost in interrupts — for the device where that question has an
    answer.

    One device per row would be the obvious shape and would be dishonest, because only one of the
    two rows could be filled in. The console's interrupt count is not in this table and the reason
    is the chapter.
    """
    run = load_result(name)["summary"]["intrload"]
    rows = [
        ["Block operations the workload performed", run["block_operations"]],
        ["Interrupts the disk raised", run["disk_interrupts"]],
        ["Characters the workload asked to be written", run["chars_requested"]],
        ["Times it had to stop and wait for the device", run["times_the_writer_had_to_wait"]],
        ["Characters arriving from the keyboard", run["chars_received"]],
    ]
    return render_table(["What happened", "Count"], rows)


def lock_primitives_table(name: str) -> str:
    """What xv6's lock is made of, as built.

    The instruction counts are what each function *contains*, error paths included — xv6 checks
    on every acquire that the caller is not already holding the lock, and panics if it is. The
    column that matters is the narrow one: how many of those instructions are doing the mutual
    exclusion.
    """
    primitives = load_result(name)["summary"]["primitives"]
    rows = [
        [
            f"`{symbol}`",
            data["instructions"],
            data["atomic"],
            data["fences"],
            data["csr_operations"],
        ]
        for symbol, data in sorted(primitives.items())
    ]
    return render_table(
        ["", "Instructions", "Atomic", "Fences", "CSR writes"],
        rows,
    )


def chapter_link(anchor: str) -> str:
    """A link to a chapter, labelled with the number it has today.

    Typed out, these go stale the way every other number does — and worse than usual, because
    `sync-labels.py` rewrites `chapters/*.md` and a generated fragment is not one of those. Five
    of them said `[ch13]` over `#traps-and-system-calls` for three renumberings, in tables ch21
    and ch23 print, and nothing could see it: the anchor resolved, so `--strict` was satisfied,
    and the syncer was never shown the file.

    So the anchor is the argument and the label is derived, which is the same rule the rest of the
    book follows and the only one that survives a chapter moving.
    """
    chapter = next(c for c in CHAPTERS if c.anchor == anchor)
    return f"[{chapter.label}](#{chapter.anchor})"


def switch_cost_table(name: str) -> str:
    """What a context switch moves, beside what a trap moves.

    The comparison is the content, so both are in one table. The trap figure is loaded rather than
    repeated, so the two cannot disagree; `run_traps --check` keeps that one current.
    """
    swtch = load_result(name)["summary"]["swtch"]
    trap = load_result("traps-xv6")["summary"]["path"]
    rows = [
        ["Registers a context switch saves", swtch["registers_saved"]],
        [
            f"Registers a trap saves ({chapter_link('traps-and-system-calls')})",
            trap["uservec"]["register_stores"],
        ],
        ["Bytes a switch moves, in and out", swtch["bytes_moved"]],
        ["Instructions in `swtch`", swtch["instructions"]],
    ]
    return render_table(["What a switch costs to arrange", "Count"], rows)


def switch_census_table(name: str) -> str:
    """The one switch count a workload decides."""
    census = load_result(name)["summary"]["census"]
    rows = [
        ["Children created and exited", census["children_created"]],
        [
            "Switches out of a process that is not coming back",
            census["switches_out_of_an_exiting_process"],
        ],
    ]
    return render_table(["What the workload caused", "Count"], rows)


def block_amplification_table(name: str) -> str:
    """What reached the disk, for a program that wrote one byte and one that wrote none.

    Three columns because the third is the only one that means anything: the two runs differ by a
    single `write` call, so the difference is the byte's and everything else cancels.
    """
    run = load_result(name)["summary"]["blockload"]
    quiet, byte, alone = (
        run["creating_an_empty_file"],
        run["and_writing_one_byte"],
        run["the_byte_alone"],
    )
    rows = [
        [label, quiet[key], byte[key], alone[key]]
        for label, key in (
            ("Blocks read from the disk", "reads"),
            ("Blocks written to the disk", "writes"),
            ("Blocks entered in the log", "logged"),
            ("Transactions committed", "commits"),
        )
    ]
    return render_table(["", "No bytes written", "One byte written", "The byte alone"], rows)


def block_cost_table(name: str) -> str:
    """The amplification, in the units the question was asked in."""
    run = load_result(name)["summary"]["blockload"]
    rows = [
        ["Bytes the program wrote", 1],
        ["Bytes the disk was given, because of that byte", run["bytes_written_for_one_byte"]],
        [
            "Bytes the disk was given for a file with nothing in it",
            run["bytes_written_for_no_bytes"],
        ],
    ]
    return render_table(["", "Bytes"], rows)


def bridge_agreement_table(name: str) -> str:
    """Everything the two targets agree about, which is everything they can be asked."""
    summary = load_result(name)["summary"]
    agreed, instructions = summary["agreed"], summary["instructions"]
    rows = [
        ["The answer both routes computed", agreed["sequential"]],
        ["Elements walked", agreed["cells"]],
        [
            "Instructions in the sequential route (RISC-V)",
            instructions["riscv64"]["sysfs_bridge_sequential"],
        ],
        [
            "Instructions in the chased route (RISC-V)",
            instructions["riscv64"]["sysfs_bridge_chased"],
        ],
        [
            "Instructions in the sequential route (AArch64)",
            instructions["aarch64"]["sysfs_bridge_sequential"],
        ],
        [
            "Instructions in the chased route (AArch64)",
            instructions["aarch64"]["sysfs_bridge_chased"],
        ],
    ]
    return render_table(["What both targets say", "Value"], rows)


def bridge_cost_table(name: str) -> str:
    """What the two routes actually cost, once the board has said.

    Written before the measurement exists, so that landing it is one command rather than a
    rewrite. The columns are the ones the chapter's argument needs: the structural prediction, the
    measured result, and the ratio between them — which is the size of the error and the reason
    Part V exists.
    """
    run = load_result(name)["summary"]["bridge"]
    rows = [
        ["Sequential route", run["sequential_ns"]],
        ["Chased route", run["chased_ns"]],
        ["Measured ratio", f"{run['chased_ns'] / run['sequential_ns']:.1f}x"],
        ["Ratio the instruction counts predict", f"{run['predicted_ratio']:.1f}x"],
    ]
    return render_table(["", "Nanoseconds per element"], rows)


def clock_table(name: str) -> str:
    """What the instrument costs and what it can resolve, before anything is measured with it."""
    clock = load_result(name)["summary"]["clock"]
    rows = [
        ["Cost of reading the clock", f"{clock['cost_ns']} ns"],
        ["Smallest change the clock ever reports", f"{clock['resolution_ns']} ns"],
        ["Work that would be half instrument", f"{clock['cost_ns']} ns"],
    ]
    return render_table(["", "Measured"], rows)


def spread_table(name: str) -> str:
    """One fixed workload, many times. The row that is not there is "the time it took"."""
    spread = load_result(name)["summary"]["spread"]
    rows = [
        ["Repetitions", spread["count"]],
        ["Fastest", f"{spread['min']} ns"],
        ["Median", f"{spread['median']} ns"],
        ["90th percentile", f"{spread['p90']} ns"],
        ["Slowest", f"{spread['max']} ns"],
        ["Mean", f"{spread['mean']} ns"],
        ["Slowest over fastest", f"{spread['max'] / spread['min']:.1f}x"],
    ]
    return render_table(["", "Nanoseconds"], rows)


def bias_table(name: str) -> str:
    """The same work, three times, differing only in something that cannot matter."""
    bias = load_result(name)["summary"]["bias"]
    rows = [
        [f"{padding} bytes of stack claimed first", f"{run['min']} ns", f"{run['median']} ns"]
        for padding, run in sorted(bias.items(), key=lambda kv: int(kv[0]))
    ]
    return render_table(["What was changed", "Fastest", "Median"], rows)


def hierarchy_levels_table(name: str) -> str:
    """Latency against working-set size. The steps are the levels, and they were not looked up."""
    rows = [
        [f"{point['bytes'] // 1024} KiB", f"{point['ns']} ns"]
        for point in load_result(name)["summary"]["sizes"]
    ]
    return render_table(["Working set", "Nanoseconds per dependent load"], rows)


def hierarchy_line_table(name: str) -> str:
    """Latency against stride. The step is the line size, and it is the same for every level."""
    rows = [
        [f"{point['bytes']} bytes", f"{point['ns']} ns"]
        for point in load_result(name)["summary"]["stride"]
    ]
    return render_table(["Stride", "Nanoseconds per dependent load"], rows)


def hierarchy_vendor_table(name: str) -> str:
    """What the machine said, beside what the vendor said.

    They are allowed to disagree, and where they do the measurement wins — a specification is a
    claim about a product line and a measurement is a statement about the silicon in front of you.
    """
    measured = load_result(name)["summary"]["derived"]
    rows = [
        [label, f"{measured[key]}", measured[f"{key}_vendor"]]
        for label, key in (
            ("Cache line", "line_bytes"),
            ("First level", "l1_bytes"),
            ("Second level", "l2_bytes"),
            ("Last level", "l3_bytes"),
        )
    ]
    return render_table(["", "Measured", "Vendor's figure"], rows)


def loop_variants_table(name: str) -> str:
    """Five hand-optimisations of one loop, and what the compiler made of each.

    Read across a row to see whether the source change survived; read down the `-O2` column to see
    how many distinct programs the five sources actually are.
    """
    summary = load_result(name)["summary"]
    counts = summary["instructions"]
    levels = list(counts)
    variants = list(counts[levels[0]])
    rows = [
        [f"`{v.removeprefix('sysfs_loop_')}`", *[counts[level][v] for level in levels]]
        for v in variants
    ]
    rows.append(["**distinct programs**", *[summary["distinct_shapes"][level] for level in levels]])
    return render_table(["Written as", *levels], rows)


def loop_cost_table(name: str) -> str:
    """What the surviving differences cost, once the board has said."""
    run = load_result(name)["summary"]["loops"]
    rows = [[f"`{variant}`", f"{ns} ns per element"] for variant, ns in sorted(run.items())]
    return render_table(["Written as", "Measured"], rows)


def pipeline_shapes_table(name: str) -> str:
    """What the core is given: instructions, branches, and branches the compiler removed."""
    shapes = load_result(name)["summary"]["shapes"]
    order = (
        "sysfs_sum_chain1",
        "sysfs_sum_chain2",
        "sysfs_sum_chain4",
        "sysfs_sum_chain8",
        "sysfs_count_over",
        "sysfs_count_over_calling",
    )
    rows = [
        [
            f"`{n.removeprefix('sysfs_')}`",
            shapes[n]["instructions"],
            shapes[n]["conditional_branches"],
            shapes[n]["if_converted"],
        ]
        for n in order
    ]
    return render_table(["", "Instructions", "Conditional branches", "Branches removed"], rows)


def pipeline_cost_table(name: str) -> str:
    """What the core did with it, once the board has said."""
    run = load_result(name)["summary"]
    rows = [
        [f"`{variant.removeprefix('sysfs_')}`", f"{data['ns']} ns", f"{data['ipc']:.2f}"]
        for variant, data in sorted(run["variants"].items())
    ]
    return render_table(["", "Nanoseconds per element", "Instructions per cycle"], rows)


def mispredict_table(name: str) -> str:
    """Misprediction rate against how predictable the data is, and the cost derived from it."""
    run = load_result(name)["summary"]["branches"]
    rows = [
        [
            f"{point['predictable_percent']}% predictable",
            f"{point['mispredict_percent']:.1f}%",
            f"{point['ns']} ns",
        ]
        for point in run["points"]
    ]
    rows.append(["**derived cost of one mispredict**", "", f"{run['derived_cost_ns']:.1f} ns"])
    return render_table(["Data", "Mispredicted", "Per element"], rows)


def sharing_layout_table(name: str) -> str:
    """Two counters, two layouts, and the only question that decides whether cores fight."""
    layouts = load_result(name)["summary"]["layouts"]
    rows = [
        [
            f"`{which}`",
            f"{layouts[which]['size']} bytes",
            " and ".join(str(o) for o in layouts[which]["offsets"]),
            "yes" if layouts[which]["same_line"] else "no",
        ]
        for which in ("packed", "padded")
    ]
    return render_table(["", "Size", "Offsets", "Same cache line"], rows)


def sharing_cost_table(name: str) -> str:
    """What sharing a line costs, once four cores have said."""
    run = load_result(name)["summary"]["sharing"]
    rows = [
        [f"{point['threads']} threads, `{point['layout']}`", f"{point['ns']} ns per increment"]
        for point in run["points"]
    ]
    return render_table(["", "Measured"], rows)


def atomics_cost_table(name: str) -> str:
    """What each ordering costs, uncontended and contended."""
    run = load_result(name)["summary"]["atomics"]
    rows = [
        [f"`{op}`", f"{data['uncontended_ns']} ns", f"{data['contended_ns']} ns"]
        for op, data in sorted(run.items())
    ]
    return render_table(["Operation", "One core", "Four cores"], rows)


def os_model_table(name: str) -> str:
    """Part IV's structural account of three kernel services, assembled in one place.

    Every figure here was measured on the xv6 target and is already in the book; gathering them is
    what makes the comparison with Linux a comparison rather than a fresh set of numbers. `name`
    is unused: the sources are the four results named below, and the conditions line comes from
    the one this figure is declared against.
    """
    traps = load_result("traps-xv6")["summary"]
    switch = load_result("switch-xv6")["summary"]["swtch"]
    faults = load_result("faults-xv6")["summary"]["faultload"]
    rows = [
        [
            "System call",
            f"{traps['path']['uservec']['instructions'] + traps['path']['userret']['instructions']} instructions of trap path",
            chapter_link("traps-and-system-calls"),
        ],
        [
            "…of which registers moved",
            f"{traps['path']['uservec']['register_stores'] + traps['path']['userret']['register_loads']}",
            chapter_link("traps-and-system-calls"),
        ],
        [
            "Page fault",
            f"{faults['load_faults'] + faults['store_faults']} for {faults['touched_lazy']} first touches",
            chapter_link("page-faults-as-a-feature"),
        ],
        [
            "Context switch",
            f"{switch['registers_saved']} registers, {switch['bytes_moved']} bytes",
            chapter_link("scheduling-and-context-switches"),
        ],
    ]
    return render_table(["Service", "What Part IV established", "Where"], rows)


def os_cost_table(name: str) -> str:
    """What Linux charges for the same three, once the board has said.

    Every row carries a baseline, because a duration on its own is not a cost. "A system call
    takes N nanoseconds" is only useful beside what the cheapest thing the machine can do takes,
    and the ratio is what survives a change of hardware.
    """
    run = load_result(name)["summary"]["services"]
    rows = [
        [f"`{service}`", f"{data['ns']} ns", data["baseline"], f"×{data['ratio']}"]
        for service, data in sorted(run.items())
    ]
    return render_table(["Service", "Measured", "Against", "Ratio"], rows)


def fault_cost_table(name: str) -> str:
    """A minor fault and a major one, which differ by what the kernel had to go and find."""
    run = load_result(name)["summary"]["faults"]
    rows = [
        [kind, f"{data['ns']} ns", data["satisfied_from"]]
        for kind, data in sorted(run.items(), key=lambda item: item[1]["ns"])
    ]
    return render_table(["Fault", "Measured", "Satisfied from"], rows)


def vdso_table(name: str) -> str:
    """The same request, with and without the privilege change.

    The `route` column is the measurement's whole point: two calls that are indistinguishable in
    C, one of which enters the kernel and one of which does not.
    """
    run = load_result(name)["summary"]["routes"]
    rows = [
        [f"`{call}`", data["route"], f"{data['ns']} ns"]
        for call, data in sorted(run.items(), key=lambda item: item[1]["ns"])
    ]
    return render_table(["Call", "Route", "Measured"], rows)


def tally_census_table(name: str) -> str:
    """What the program under ch27's profiler does, counted before anybody times it.

    Written as a prediction. Everything here is a property of the program and its sizes, so it is
    the same on every machine, and the chapter's method is to commit to it and then find out
    whether the profile agrees.
    """
    run = load_result(name)["summary"]
    lines_in_table = run["table_bytes"] // run["line_bytes"]
    rows = [
        ["Records", f"{run['records']:,}"],
        ["Counters in the table", f"{run['entries']:,} ({run['table_bytes']:,} bytes)"],
        ["Counters the keys actually reach", f"{run['distinct_keys']:,}"],
        [
            "Cache lines they reach",
            f"{run['lines_touched']:,}"
            + (" — every line in the table" if run["lines_touched"] == lines_in_table else ""),
        ],
        [
            "Decode's conditional, taken",
            f"{run['decode_taken']:,} of {run['records']:,}",
        ],
        [
            "Table in play at once, partitioned",
            f"{run['slice_entries']:,} ({run['slice_bytes']:,} bytes)",
        ],
        [
            "Key traffic partitioning adds",
            f"{run['key_reads']:,} reads, {run['key_writes']:,} writes",
        ],
    ]
    return render_table(["Counted before the profile", "Value"], rows)


def profile_table(name: str) -> str:
    """Where the samples landed, before and after the change."""
    run = load_result(name)["summary"]["symbols"]
    rows = [
        [f"`{symbol}`", f"{data['before_pct']}%", f"{data['after_pct']}%"]
        for symbol, data in sorted(
            run.items(), key=lambda item: item[1]["before_pct"], reverse=True
        )
    ]
    return render_table(["Symbol", "Before", "After"], rows)


def skid_table(name: str) -> str:
    """The instruction the samples were attributed to, and the one that was waiting."""
    run = load_result(name)["summary"]["instructions"]
    rows = [
        [f"`{entry['text']}`", f"+{entry['offset']}", f"{entry['samples_pct']}%"] for entry in run
    ]
    return render_table(["Instruction", "Offset", "Samples"], rows)


def vector_loops_table(name: str) -> str:
    """Five loops and three builds: which of them the compiler widened, and when.

    Instructions and vector instructions in the same cell, because neither is the answer alone. A
    loop that widened has both a handful of vector instructions and several times as many
    instructions overall — the width is in the middle and the rest is getting there.
    """
    run = load_result(name)["summary"]
    headers = {"o2": "`-O2`", "o3": "`-O3`", "o3fast": "`-O3 -ffast-math`"}
    levels = [level for level in ("o2", "o3", "o3fast") if level in run["levels"]]
    rows = [
        [f"`{symbol}`"]
        + [
            f"{run['loops'][symbol][level]['instructions']}"
            f" ({run['loops'][symbol][level]['vector']} vector)"
            for level in levels
        ]
        for symbol in sorted(run["loops"])
    ]
    return render_table(["Loop", *(headers[level] for level in levels)], rows)


def vector_speedup_table(name: str) -> str:
    """What each loop actually gained, beside what its lane count allows.

    The bound column is the point. A speedup printed on its own invites the reader to be pleased
    with it; printed beside the most the width could possibly buy, it invites the only useful
    question, which is where the rest went.
    """
    run = load_result(name)["summary"]["loops"]
    rows = [
        [f"`{symbol}`", f"×{data['speedup']}", f"×{data['bound']}", f"{data['achieved_pct']}%"]
        for symbol, data in sorted(run.items())
    ]
    return render_table(["Loop", "Measured", "Arithmetic bound", "Of the bound"], rows)


def xv6_file_map_table(name: str) -> str:
    """Which file of the kernel each chapter of Part IV reads, and how long it is.

    Ordered by chapter rather than alphabetically, because the reader arrives here from a chapter
    and wants its rows together. The line counts are walked from the submodule at its pinned
    commit, so they are numbers a reader can check with `wc -l` on the tree they have.
    """
    run = load_result(name)["summary"]
    rows = [
        [
            f"`kernel/{file}`",
            run["files"][file]["lines"],
            f"[{_by_anchor[entry['chapter']].label}](#{entry['chapter']})",
            entry["for"],
        ]
        for file, entry in sorted(
            run["reads"].items(),
            key=lambda item: (_by_anchor[item[1]["chapter"]].number, item[0]),
        )
    ]
    return render_table(["File", "Lines", "Read by", "For"], rows)


def xv6_kernel_size_table(name: str) -> str:
    """How much kernel there is, and how much of it this book actually opens."""
    run = load_result(name)["summary"]
    mapped = len(run["reads"])
    rows = [
        ["Files in `kernel/`", len(run["files"])],
        ["Lines in all of them", run["total_lines"]],
        ["Files a chapter reads", mapped],
        ["Lines in those", run["mapped_lines"]],
        ["Files nothing in this book opens", len(run["files"]) - mapped],
    ]
    return render_table(["The kernel, counted", "Value"], rows)


def kernel_absences_table(name: str) -> str:
    """What the kernel does not have, counted from the kernel that is checked in.

    An absence is harder to believe than a presence, which is why each row carries the number that
    settles it rather than the word "none". The instruction count is there to give the zero a
    denominator: no floating point in nine thousand instructions is a decision, and no floating
    point in nine is an accident of a small sample.
    """
    run = load_result(name)["summary"]
    rows = [
        ["Instructions in the kernel", f"{run['kernel']['instructions']:,}"],
        ["…that name a floating-point register", run["kernel"]["floating_point"]],
        ["Heap functions it defines", len(run["heap_functions"])],
        ["C library functions it reimplements", run["reimplemented_count"]],
    ]
    return render_table(["The kernel as built", "Value"], rows)


def kernel_pools_table(name: str) -> str:
    """The compile-time bounds that are this kernel's allocator.

    Every one of them is the length of an array that exists for the whole run. A hosted program
    would ask for memory and check whether it arrived; a kernel this size decides the maximum in
    advance and returns a failure when the pool is full.
    """
    run = load_result(name)["summary"]["pool_bounds"]
    meaning = {
        "NPROC": "processes",
        "NCPU": "harts",
        "NOFILE": "open files, per process",
        "NFILE": "open files, system-wide",
        "NINODE": "in-memory inodes",
        "NDEV": "device drivers",
        "NBUF": "disk blocks cached",
        "MAXARG": "arguments to `exec`",
    }
    rows = [[f"`{bound}`", run[bound], meaning.get(bound, "")] for bound in sorted(run)]
    return render_table(["Bound", "Value", "What it limits"], rows)


def first_program_table(name: str) -> str:
    """What ch01's first complete program prints, so the chapter can quote rather than assert.

    No address appears here. One would differ on every run; the distance between two does not,
    and the distance is what the chapter is about.
    """
    run = load_result(name)["summary"]
    rows = [
        ["`value`", run["value"]],
        ["`*&value` — the same thing again", run["roundtrip"]],
        ["Bytes from one `int32_t` to the next", run["steps"]["int32"]],
        ["Bytes from one `int64_t` to the next", run["steps"]["int64"]],
    ]
    return render_table(["What the program printed", "Value"], rows)


# -- Part II: the machine with nothing on it ----------------------------------------------

#: Which fields of a `bare` result a chapter shows, in what order, and how to read each one.
#:
#: Keyed by result, because in Part II one program answers one chapter's question and the table
#: is the answer. ``bool`` renders yes or no: most of what these programs report is a claim being
#: true, and printing 1 for it would make a table of ones that nobody reads.
BARE_TABLES: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "trap-bare": (
        "One trap, start to finish",
        [
            ("mtvec_is_handler", "`mtvec` holds the handler's address", "bool"),
            ("cause", "`mcause`", "int"),
            ("cause_is_ecall", "…which is *environment call from machine mode*", "bool"),
            ("mepc_is_the_ecall", "`mepc` is the address **of** the `ecall`, not after it", "bool"),
            ("mepc_advance", "Bytes the handler must add before returning", "int"),
            ("register_survived", "A register set before the trap, still set after it", "bool"),
            ("taken", "Traps taken", "int"),
        ],
    ),
    "privilege-bare": (
        "An interrupt nobody asked for, and a refusal",
        [
            ("interrupt_arrived", "The timer interrupted a loop that asked for nothing", "bool"),
            ("cause_is_asynchronous", "`mcause`'s top bit is set: asynchronous", "bool"),
            ("interrupt_code", "Cause code (machine timer)", "int"),
            ("machine_register_refused", "Supervisor mode reading a machine register", "bool"),
            ("refusal_code", "…refused with cause", "int"),
            ("refusal_is_illegal_instruction", "…which is *illegal instruction*", "bool"),
            ("back_in_machine_mode", "The handler returned us to machine mode", "bool"),
        ],
    ),
    "paging-bare": (
        "One page table of three entries",
        [
            ("entries_used", "Entries in the table", "int"),
            ("reached_supervisor", "Translation is on, and the program still runs", "bool"),
            ("alias_reads_the_same", "Two addresses, one byte", "bool"),
            ("alias_distance_gigabytes", "Gigabytes between those two addresses", "int"),
            ("machine_mode_ignores_satp", "Machine mode read it untranslated", "bool"),
        ],
    ),
    "harts-bare": (
        "What a second core costs an unguarded counter",
        [
            ("increments_attempted", "Increments performed", "int"),
            ("counter_after", "What the counter holds", "int"),
            ("updates_lost", "Updates lost", "int"),
            ("atomic_increments_attempted", "Increments performed, atomically", "int"),
            ("atomic_counter_after", "What that counter holds", "int"),
            ("atomic_updates_lost", "Updates lost", "int"),
        ],
    ),
    "syscall-bare": (
        "What crosses the boundary",
        [
            ("registers_in_frame", "Registers the handler saves by hand", "int"),
            ("calls_dispatched", "Calls dispatched", "int"),
            ("number_crossed", "A call number chose what happened", "bool"),
            ("result_returned", "3 and 4 went in; this came back", "int"),
            (
                "caller_register_in_frame",
                "The caller's register, read out of the saved frame",
                "bool",
            ),
            ("caller_register_intact", "…and unchanged when the caller resumed", "bool"),
            ("unknown_call_refused", "Calls refused as unknown", "int"),
            ("unknown_returned_error", "…by returning an error, not by stopping", "bool"),
        ],
    ),
    "descriptors-bare": (
        "One table, two destinations, one position",
        [
            ("descriptor_slots", "Descriptor slots", "int"),
            ("open_file_slots", "Open-file slots", "int"),
            ("backends", "Kinds of thing a descriptor can find", "int"),
            (
                "same_call_reached_both",
                "One `write`, two destinations, one register different",
                "bool",
            ),
            ("cursor_after_writing", "Where the position is after writing six bytes", "int"),
            ("read_without_rewinding", "Bytes a read returns from there", "int"),
            ("read_after_rewinding", "…and after moving the position back to the start", "int"),
            ("memory_kept_the_bytes", "The bytes read back are the bytes written", "bool"),
            ("closed_slot_refused", "An unopened descriptor is refused", "bool"),
            ("dup_shares_the_open_file", "A duplicate is a second name, not a copy", "bool"),
            ("cursor_after_dup_write", "Position after one byte through the duplicate", "int"),
            (
                "dup_appended_rather_than_overwrote",
                "…which landed after the six, not on them",
                "bool",
            ),
            ("read_everything", "Bytes in the array altogether", "int"),
        ],
    ),
    "fork-bare": (
        "Two processes from one",
        [
            ("processes", "Processes", "int"),
            ("address_spaces", "Address spaces", "int"),
            ("pages_copied", "Pages copied", "int"),
            ("parent_result", "What `fork` returned to the parent", "int"),
            ("child_result", "What it returned to the child", "int"),
            ("both_ran", "Both processes ran", "bool"),
            ("child_saw_the_parents_byte", "The child began with the parent's data", "bool"),
            ("childs_write_stayed_in_its_own_page", "…and its writes stayed its own", "bool"),
        ],
    ),
}


def bare_claims_table(name: str) -> str:
    """What one bare-metal program reported, as the chapter's answer to its own question."""
    run = load_result(name)["summary"]
    heading, rows = BARE_TABLES[name]

    def cell(field: str, kind: str):
        value = run[field]
        if kind != "bool":
            return value
        return "yes" if value else "no"

    body = [[label, cell(field, kind)] for field, label, kind in rows if field in run]
    return render_table([heading, "Observed"], body)
