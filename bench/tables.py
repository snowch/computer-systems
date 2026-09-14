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
    ]
    return render_table(["What", "This board"], rows)
