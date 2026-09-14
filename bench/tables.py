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
