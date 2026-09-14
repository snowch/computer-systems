"""Every figure the book contains, declared in one place.

One entry per table and per diagram, so a chapter cannot quietly cite a different run than the
one its prose discusses. ``scripts/render-figures.py`` turns these into files under
``chapters/_generated/`` and ``chapters/_figures/``, which chapters pull in with ``{include}``
and ``{figure}``; ``scripts/verify-numbers.py`` fails the build when a committed fragment no
longer matches what the results say.

## Pending figures

Part III is measured on hardware that is not attached to CI and never will be. A figure whose
measurement has not been taken yet is declared here with a ``pending`` reason, and renders as a
warning naming the command that would produce it. That is deliberately not the same thing as a
placeholder number:

* nothing is invented — the fragment contains no figures at all, so a draft can never be mistaken
  for a measurement, in the site or in the PDF;
* the prose around it is written as though the numbers were there, so landing them is a
  one-command change rather than a rewrite;
* ``verify-numbers.py`` **fails** if a pending figure's result file exists, so a measurement that
  has landed cannot be left marked as missing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bench import tables
from bench.diagrams import (
    address_space_cost,
    dispatch_table,
    fault_decision,
    interrupt_sources,
    sections_to_segments,
    stack_frame,
    struct_padding,
    sv39_walk,
    toolchain_stages,
    trap_path,
    two_target_map,
)


@dataclass(frozen=True)
class Table:
    """A markdown fragment rendered from one committed result."""

    render: Callable[[str], str]
    result: str
    #: None means "take the conditions line from `result`"; a name overrides it.
    conditions_from: str | None = None
    #: Why this has not been measured, and what to run. None means it has been.
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.pending is None else ()


@dataclass(frozen=True)
class Diagram:
    """An SVG figure drawn by :mod:`bench.diagrams`.

    ``result`` is optional and changes what the drawing function is handed. Without it the figure
    is a statement about a mechanism — the four stages of a toolchain, the division of labour
    between two targets — and needs no data. With it, the function is passed the result's name and
    draws from stamped numbers, which is how a measured layout or a latency curve gets to be a
    picture without anybody typing a coordinate.

    The distinction matters to more than tidiness: a diagram that reads a result depends on it, so
    ``scripts/verify-numbers.py`` must know to check that result exists and is current. That is
    what :attr:`sources` is for, and why it is not always empty.
    """

    draw: Callable[..., str]
    alt: str
    #: The stamped result this figure draws from, if any.
    result: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.result else ()

    def render(self) -> str:
        return self.draw(self.result) if self.result else self.draw()


@dataclass(frozen=True)
class Listing:
    """One function's machine code, on every architecture the book shows it on.

    Not a table and not a drawing: a fenced block of objdump output, taken from a ``kind: listing``
    result (``bench/disasm.py``). It is here for the same reason tables are — so that a chapter
    cannot show machine code that no compiler produced, and so that CI notices when the compiler
    stops producing it.

    ``results`` is ordered, and the order is editorial: the architectures appear in the sequence
    the surrounding prose discusses them.
    """

    symbol: str
    results: tuple[str, ...]

    @property
    def sources(self) -> tuple[str, ...]:
        return self.results


#: The board runs Part III. Repeating the instruction in every pending reason would be noise, so
#: it lives here and each entry says what specifically is missing.
BOARD = "run `make bench-board` on the reference machine and commit the result"

FIGURES: dict[str, Table | Diagram | Listing] = {
    # -- ch00 ---------------------------------------------------------------------------
    "ch00-targets": Diagram(
        draw=two_target_map,
        alt="The xv6 and host targets side by side, with what each can and cannot answer.",
    ),
    "ch00-xv6-environment": Table(
        render=tables.xv6_environment_table,
        result="setup-xv6",
    ),
    "ch00-probe-types": Table(
        render=tables.probe_types_table,
        result="setup-xv6",
    ),
    "ch00-probe-layouts": Table(
        render=tables.probe_layout_table,
        result="setup-xv6",
    ),
    "ch00-clamp": Listing(
        symbol="sysfs_clamp",
        # RISC-V first: it is the target the reader has already booted by this point in ch00.
        results=("shapes-riscv64", "shapes-aarch64"),
    ),
    # -- ch01 ---------------------------------------------------------------------------
    "ch01-stages": Diagram(
        draw=toolchain_stages,
        alt="The four stages of the toolchain, what each hands on, and what each discards.",
    ),
    "ch01-stage-sizes": Table(
        render=tables.stage_sizes_table,
        result="stagewalk-riscv64",
    ),
    "ch01-linking": Table(
        render=tables.linking_cost_table,
        result="stagewalk-riscv64",
    ),
    "ch01-folded": Listing(
        symbol="sysfs_sum_folded",
        results=("stages-riscv64",),
    ),
    "ch01-counted": Listing(
        symbol="sysfs_sum_counted",
        results=("stages-riscv64",),
    ),
    # -- ch02 ---------------------------------------------------------------------------
    "ch02-padding": Diagram(
        draw=struct_padding,
        alt="Both structs drawn byte by byte, with the bytes no member uses marked.",
        result="setup-xv6",
    ),
    "ch02-signed-grows": Listing(
        symbol="sysfs_signed_grows",
        results=("signedness-riscv64",),
    ),
    "ch02-unsigned-grows": Listing(
        symbol="sysfs_unsigned_grows",
        results=("signedness-riscv64",),
    ),
    "ch02-signed-quarter": Listing(
        symbol="sysfs_signed_quarter",
        results=("signedness-riscv64",),
    ),
    "ch02-unsigned-quarter": Listing(
        symbol="sysfs_unsigned_quarter",
        results=("signedness-riscv64",),
    ),
    # -- ch03 ---------------------------------------------------------------------------
    "ch03-dispatch": Diagram(
        draw=dispatch_table,
        alt="A table of function pointers, each slot holding an address of code stored elsewhere.",
    ),
    "ch03-plain-reads": Listing(
        symbol="sysfs_read_four",
        results=("addresses-riscv64",),
    ),
    "ch03-volatile-reads": Listing(
        symbol="sysfs_read_four_volatile",
        results=("addresses-riscv64",),
    ),
    "ch03-array-parameter": Listing(
        symbol="sysfs_sum_array",
        results=("addresses-riscv64",),
    ),
    "ch03-private-call": Listing(
        symbol="sysfs_uses_private",
        results=("addresses-riscv64",),
    ),
    "ch03-indirect-call": Listing(
        symbol="sysfs_call_through",
        results=("addresses-riscv64",),
    ),
    # -- ch04 ---------------------------------------------------------------------------
    "ch04-frame": Diagram(
        draw=stack_frame,
        alt="A stack frame with the saved frame pointer and return address slots marked.",
    ),
    "ch04-frames": Table(
        render=tables.frame_sizes_table,
        result="framesizes-riscv64",
    ),
    "ch04-leaf": Listing(
        symbol="sysfs_leaf",
        results=("frames-riscv64",),
    ),
    "ch04-calls-out": Listing(
        symbol="sysfs_calls_out",
        results=("frames-riscv64",),
    ),
    # -- ch05 ---------------------------------------------------------------------------
    "ch05-segments": Diagram(
        draw=sections_to_segments,
        alt="Eighteen ELF sections collapsing into two loadable segments.",
        result="elf-xv6",
    ),
    "ch05-segment-table": Table(
        render=tables.elf_segments_table,
        result="elf-xv6",
    ),
    "ch05-shape": Table(
        render=tables.elf_shape_table,
        result="elf-xv6",
    ),
    # -- ch06 ---------------------------------------------------------------------------
    "ch06-trap-path": Diagram(
        draw=trap_path,
        alt="One system call from ecall to sret, with the state movement at each end.",
        result="traps-xv6",
    ),
    "ch06-path-counts": Table(
        render=tables.trap_path_table,
        result="traps-xv6",
    ),
    "ch06-census": Table(
        render=tables.trap_census_table,
        result="traps-xv6",
    ),
    # -- ch07 ---------------------------------------------------------------------------
    "ch07-walk": Diagram(
        draw=sv39_walk,
        alt="A 64-bit virtual address split into three nine-bit indices and a twelve-bit offset.",
        result="pagetable-xv6",
    ),
    "ch07-sv39": Table(
        render=tables.sv39_geometry_table,
        result="pagetable-xv6",
    ),
    "ch07-shape": Table(
        render=tables.pagetable_shape_table,
        result="pagetable-xv6",
    ),
    "ch07-address-spaces": Diagram(
        draw=address_space_cost,
        alt="init's two clusters of mapped pages, and the chain of tables each one forces.",
        result="pagetable-xv6",
    ),
    # -- ch08 ---------------------------------------------------------------------------
    "ch08-decision": Diagram(
        draw=fault_decision,
        alt="A page fault, the one test that decides what happens, and the two outcomes.",
        result="faults-xv6",
    ),
    "ch08-exchange": Table(
        render=tables.fault_exchange_table,
        result="faults-xv6",
    ),
    "ch08-causes": Table(
        render=tables.fault_causes_table,
        result="faults-xv6",
    ),
    # -- ch09 ---------------------------------------------------------------------------
    "ch09-sources": Diagram(
        draw=interrupt_sources,
        alt="Three interrupt sources, and which of them a fixed workload gives a fixed count for.",
        result="interrupts-xv6",
    ),
    "ch09-cost": Table(
        render=tables.interrupt_cost_table,
        result="interrupts-xv6",
    ),
    "ch00-board": Table(
        render=tables.board_identity_table,
        result="setup-host",
        pending=f"The board has not reported yet: {BOARD} (`bench/results/setup-host.json`).",
    ),
}


#: Every figure kind. A renderer that meets something not in here should fail rather than skip:
#: a figure silently missing from a chapter is the failure this whole pipeline exists to prevent.
KINDS = (Table, Diagram, Listing)


def cited_results() -> set[str]:
    """Every result file a figure reads. Pending figures cite nothing, by definition."""
    return {name for figure in FIGURES.values() for name in figure.sources}


def pending_results() -> dict[str, str]:
    """Result name -> the reason its figure is still waiting for it."""
    return {
        figure.result: figure.pending
        for figure in FIGURES.values()
        if isinstance(figure, Table) and figure.pending is not None
    }
