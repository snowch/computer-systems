"""Turning committed results into the markdown the chapters include.

Imports nothing but the standard library, on purpose: this runs in CI on every push, and a table
renderer that needs a scientific Python stack installed is a table renderer that breaks for
reasons having nothing to do with the book.

The rule these functions exist to enforce is that **no number is ever typed into prose**
(PLAN.md §6.3). If a figure appears in this book it came from a file under ``bench/results/``
that names the target, the machine, the kernel, the compiler and the flags that produced it.
"""

from __future__ import annotations

from typing import Any

from bench.stamp import load_result


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
    if toolchain.get("flags"):
        parts.append(f"`{toolchain['flags']}`")
    parts.append(result["generated_at"][:10])
    return (
        "*Conditions: "
        + "; ".join(parts)
        + f". Source: `bench/results/{name}.json`, code hash `{result['code_fingerprint']}`.*"
    )


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


def listing_label(name: str, symbol: str) -> str:
    """The line above a listing: what it is, which architecture, and how long it came out.

    Assembled from the result rather than typed, like everything else here. The instruction count
    in particular: it is the figure a chapter comparing two architectures most wants to quote, and
    a hand-typed one would be the first thing to go stale.
    """
    result = load_result(name)
    arch = result["machine"]["arch"]
    count = listing_instructions(name, symbol)
    return (
        f"**`{symbol}` compiled for {arch}** — the `{result['target']}` target's instruction set, "
        f"{count} instructions."
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
#: following Part III on a RISC-V board is supported. A key absent from this mapping is still
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
    the numbers in every other table in Part III, which is the one that matters when two of them
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
        # The two capabilities Part III is built on, and they are separate questions: a core can
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
        ["Characters the writing process handed over itself", run["chars_the_writer_moved_itself"]],
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


def switch_cost_table(name: str) -> str:
    """What a context switch moves, beside what a trap moves.

    The comparison is the content, so both are in one table. ch06's figure is loaded rather than
    repeated, so the two cannot disagree; `run_traps --check` keeps that one current.
    """
    swtch = load_result(name)["summary"]["swtch"]
    trap = load_result("traps-xv6")["summary"]["path"]
    rows = [
        ["Registers a context switch saves", swtch["registers_saved"]],
        ["Registers a trap saves ([ch06](#ch06))", trap["uservec"]["register_stores"]],
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
    Part III exists.
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
