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


def board_identity_table(name: str) -> str:
    """The board's account of itself, read from the running machine rather than a datasheet.

    A spec sheet describes a product line. ``/proc/cpuinfo`` describes the silicon that produced
    the numbers in every other table in Part III, which is the one that matters when two of them
    disagree.
    """
    result = load_result(name)
    summary = result["summary"]
    machine = result["machine"]
    cpu = machine.get("cpu", {})
    rows = [
        ["Board (device tree)", machine.get("model")],
        ["Kernel", machine.get("kernel")],
        ["ISA string", cpu.get("isa")],
        ["Microarchitecture", cpu.get("uarch")],
        ["`mvendorid` / `marchid` / `mimpid`", summary.get("ids")],
        ["Harts online", machine.get("cpus_online")],
        ["Compiler", result.get("toolchain", {}).get("cc")],
        ["`perf stat` reads hardware counters", summary.get("perf_counters_readable")],
        ["Cycle counter event", summary.get("perf_cycles_event")],
    ]
    return render_table(["What", "This board"], rows)
