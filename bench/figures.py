"""Every figure the book contains, declared in one place.

One entry per table and per diagram, so a chapter cannot quietly cite a different run than the
one its prose discusses. ``scripts/render-figures.py`` turns these into files under
``chapters/_generated/`` and ``chapters/_figures/``, which chapters pull in with ``{include}``
and ``{figure}``; ``scripts/verify-numbers.py`` fails the build when a committed fragment no
longer matches what the results say.

## Pending figures

Part V is measured on hardware that is not attached to CI and never will be. A figure whose
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
    bare_trap,
    dispatch_table,
    fault_decision,
    gigapage_alias,
    interrupt_sources,
    privilege_path,
    sampling_profile,
    sections_to_segments,
    stack_frame,
    struct_padding,
    sv39_walk,
    three_target_map,
    toolchain_stages,
    trap_path,
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


#: The board runs Part V. Repeating the instruction in every pending reason would be noise, so
#: it lives here and each entry says what specifically is missing.
BOARD = "run `make bench-board` on the reference machine and commit the result"

FIGURES: dict[str, Table | Diagram | Listing] = {
    # -- ch00 ---------------------------------------------------------------------------
    "prerequisites-and-setup-targets": Diagram(
        draw=three_target_map,
        alt="The bare, xv6 and host targets side by side, with what each can and cannot answer.",
    ),
    "prerequisites-and-setup-xv6-environment": Table(
        render=tables.xv6_environment_table,
        result="setup-xv6",
    ),
    "prerequisites-and-setup-probe-types": Table(
        render=tables.probe_types_table,
        result="setup-xv6",
    ),
    "prerequisites-and-setup-probe-layouts": Table(
        render=tables.probe_layout_table,
        result="setup-xv6",
    ),
    "reading-a-listing-clamp": Listing(
        symbol="sysfs_clamp",
        # RISC-V first: it is the target the reader has already booted by this point in ch00.
        results=("shapes-riscv64", "shapes-aarch64"),
    ),
    # -- ch09 ---------------------------------------------------------------------------
    "what-a-computer-does-with-a-program-stages": Diagram(
        draw=toolchain_stages,
        alt="The four stages of the toolchain, what each hands on, and what each discards.",
    ),
    "what-a-computer-does-with-a-program-stage-sizes": Table(
        render=tables.stage_sizes_table,
        result="stagewalk-riscv64",
    ),
    "what-a-computer-does-with-a-program-linking": Table(
        render=tables.linking_cost_table,
        result="stagewalk-riscv64",
    ),
    "what-a-computer-does-with-a-program-folded": Listing(
        symbol="sysfs_sum_folded",
        results=("stages-riscv64",),
    ),
    "what-a-computer-does-with-a-program-counted": Listing(
        symbol="sysfs_sum_counted",
        results=("stages-riscv64",),
    ),
    # -- ch10 ---------------------------------------------------------------------------
    "representing-information-padding": Diagram(
        draw=struct_padding,
        alt="Both structs drawn byte by byte, with the bytes no member uses marked.",
        result="setup-xv6",
    ),
    "representing-information-signed-grows": Listing(
        symbol="sysfs_signed_grows",
        results=("signedness-riscv64",),
    ),
    "representing-information-unsigned-grows": Listing(
        symbol="sysfs_unsigned_grows",
        results=("signedness-riscv64",),
    ),
    "representing-information-signed-quarter": Listing(
        symbol="sysfs_signed_quarter",
        results=("signedness-riscv64",),
    ),
    "representing-information-unsigned-quarter": Listing(
        symbol="sysfs_unsigned_quarter",
        results=("signedness-riscv64",),
    ),
    # -- ch03 ---------------------------------------------------------------------------
    "c-for-people-who-will-read-a-kernel-dispatch": Diagram(
        draw=dispatch_table,
        alt="A table of function pointers, each slot holding an address of code stored elsewhere.",
    ),
    "c-for-people-who-will-read-a-kernel-plain-reads": Listing(
        symbol="sysfs_read_four",
        results=("addresses-riscv64",),
    ),
    "c-for-people-who-will-read-a-kernel-volatile-reads": Listing(
        symbol="sysfs_read_four_volatile",
        results=("addresses-riscv64",),
    ),
    "c-for-people-who-will-read-a-kernel-array-parameter": Listing(
        symbol="sysfs_sum_array",
        results=("addresses-riscv64",),
    ),
    "c-for-people-who-will-read-a-kernel-private-call": Listing(
        symbol="sysfs_uses_private",
        results=("addresses-riscv64",),
    ),
    "c-for-people-who-will-read-a-kernel-indirect-call": Listing(
        symbol="sysfs_call_through",
        results=("addresses-riscv64",),
    ),
    # -- ch11 ---------------------------------------------------------------------------
    "machine-level-code-on-riscv-frame": Diagram(
        draw=stack_frame,
        alt="A stack frame with the saved frame pointer and return address slots marked.",
    ),
    "machine-level-code-on-riscv-frames": Table(
        render=tables.frame_sizes_table,
        result="framesizes-riscv64",
    ),
    "machine-level-code-on-riscv-leaf": Listing(
        symbol="sysfs_leaf",
        results=("frames-riscv64",),
    ),
    "machine-level-code-on-riscv-calls-out": Listing(
        symbol="sysfs_calls_out",
        results=("frames-riscv64",),
    ),
    # -- ch12 ---------------------------------------------------------------------------
    "linking-and-loading-segments": Diagram(
        draw=sections_to_segments,
        alt="Eighteen ELF sections collapsing into two loadable segments.",
        result="elf-xv6",
    ),
    "linking-and-loading-segment-table": Table(
        render=tables.elf_segments_table,
        result="elf-xv6",
    ),
    "linking-and-loading-shape": Table(
        render=tables.elf_shape_table,
        result="elf-xv6",
    ),
    # -- ch13 ---------------------------------------------------------------------------
    "traps-and-system-calls-trap-path": Diagram(
        draw=trap_path,
        alt="One system call from ecall to sret, with the state movement at each end.",
        result="traps-xv6",
    ),
    "traps-and-system-calls-path-counts": Table(
        render=tables.trap_path_table,
        result="traps-xv6",
    ),
    "traps-and-system-calls-census": Table(
        render=tables.trap_census_table,
        result="traps-xv6",
    ),
    # -- ch14 ---------------------------------------------------------------------------
    "virtual-memory-walk": Diagram(
        draw=sv39_walk,
        alt="A 64-bit virtual address split into three nine-bit indices and a twelve-bit offset.",
        result="pagetable-xv6",
    ),
    "virtual-memory-sv39": Table(
        render=tables.sv39_geometry_table,
        result="pagetable-xv6",
    ),
    "virtual-memory-shape": Table(
        render=tables.pagetable_shape_table,
        result="pagetable-xv6",
    ),
    "virtual-memory-address-spaces": Diagram(
        draw=address_space_cost,
        alt="init's two clusters of mapped pages, and the chain of tables each one forces.",
        result="pagetable-xv6",
    ),
    # -- ch15 ---------------------------------------------------------------------------
    "page-faults-as-a-feature-decision": Diagram(
        draw=fault_decision,
        alt="A page fault, the one test that decides what happens, and the two outcomes.",
        result="faults-xv6",
    ),
    "page-faults-as-a-feature-exchange": Table(
        render=tables.fault_exchange_table,
        result="faults-xv6",
    ),
    "page-faults-as-a-feature-causes": Table(
        render=tables.fault_causes_table,
        result="faults-xv6",
    ),
    # -- ch16 ---------------------------------------------------------------------------
    "interrupts-and-drivers-sources": Diagram(
        draw=interrupt_sources,
        alt="Three interrupt sources, and which of them a fixed workload gives a fixed count for.",
        result="interrupts-xv6",
    ),
    "interrupts-and-drivers-cost": Table(
        render=tables.interrupt_cost_table,
        result="interrupts-xv6",
    ),
    # -- ch17 ---------------------------------------------------------------------------
    "locks-and-memory-ordering-race": Listing(
        symbol="sysfs_bump_plain",
        results=("ordering-riscv64", "ordering-aarch64"),
    ),
    "locks-and-memory-ordering-atomic": Listing(
        symbol="sysfs_bump_relaxed",
        results=("ordering-riscv64", "ordering-aarch64"),
    ),
    "locks-and-memory-ordering-ordered": Listing(
        symbol="sysfs_bump_ordered",
        results=("ordering-riscv64",),
    ),
    "locks-and-memory-ordering-publish": Listing(
        symbol="sysfs_publish",
        results=("ordering-riscv64", "ordering-aarch64"),
    ),
    "locks-and-memory-ordering-primitives": Table(
        render=tables.lock_primitives_table,
        result="locks-xv6",
    ),
    # -- ch18 ---------------------------------------------------------------------------
    "scheduling-and-context-switches-swtch": Table(
        render=tables.switch_cost_table,
        result="switch-xv6",
    ),
    "scheduling-and-context-switches-census": Table(
        render=tables.switch_census_table,
        result="switch-xv6",
    ),
    # -- ch19 ---------------------------------------------------------------------------
    "the-file-system-amplification": Table(
        render=tables.block_amplification_table,
        result="blocks-xv6",
    ),
    "the-file-system-cost": Table(
        render=tables.block_cost_table,
        result="blocks-xv6",
    ),
    # -- ch20 ---------------------------------------------------------------------------
    "the-same-program-on-both-targets-sequential": Listing(
        symbol="sysfs_bridge_sequential",
        results=("bridge-riscv64", "bridge-aarch64"),
    ),
    "the-same-program-on-both-targets-chased": Listing(
        symbol="sysfs_bridge_chased",
        results=("bridge-riscv64", "bridge-aarch64"),
    ),
    "the-same-program-on-both-targets-agreement": Table(
        render=tables.bridge_agreement_table,
        result="bridge-both",
    ),
    "the-same-program-on-both-targets-cost": Table(
        render=tables.bridge_cost_table,
        result="bridge-host",
    ),
    # -- ch21 ---------------------------------------------------------------------------
    "measuring-clock": Table(
        render=tables.clock_table,
        result="measuring-host",
    ),
    "measuring-spread": Table(
        render=tables.spread_table,
        result="measuring-host",
    ),
    "measuring-bias": Table(
        render=tables.bias_table,
        result="measuring-host",
    ),
    # -- ch22 ---------------------------------------------------------------------------
    "the-memory-hierarchy-levels": Table(
        render=tables.hierarchy_levels_table,
        result="hierarchy-host",
    ),
    "the-memory-hierarchy-line": Table(
        render=tables.hierarchy_line_table,
        result="hierarchy-host",
    ),
    "the-memory-hierarchy-reach": Table(
        render=tables.hierarchy_reach_table,
        result="hierarchy-host",
    ),
    "the-memory-hierarchy-vendor": Table(
        render=tables.hierarchy_vendor_table,
        result="hierarchy-host",
    ),
    # -- ch23 ---------------------------------------------------------------------------
    "optimising-code-variants": Table(
        render=tables.loop_variants_table,
        result="loops-aarch64",
    ),
    "optimising-code-cost": Table(
        render=tables.loop_cost_table,
        result="loops-host",
    ),
    # -- ch24 ---------------------------------------------------------------------------
    "the-cpu-shapes": Table(
        render=tables.pipeline_shapes_table,
        result="pipeline-shapes",
    ),
    "the-cpu-ilp": Table(
        render=tables.pipeline_cost_table,
        result="pipeline-host",
    ),
    "the-cpu-branches": Table(
        render=tables.mispredict_table,
        result="pipeline-host",
    ),
    # -- ch25 ---------------------------------------------------------------------------
    "memory-ordering-on-real-hardware-layout": Table(
        render=tables.sharing_layout_table,
        result="sharing-layout",
    ),
    "memory-ordering-on-real-hardware-sharing": Table(
        render=tables.sharing_cost_table,
        result="sharing-host",
    ),
    "memory-ordering-on-real-hardware-atomics": Table(
        render=tables.atomics_cost_table,
        result="sharing-host",
    ),
    # -- ch26 ---------------------------------------------------------------------------
    "the-os-layers-cost-model": Table(
        render=tables.os_model_table,
        result="traps-xv6",
    ),
    "the-os-layers-cost-trap": Listing(
        symbol="sysfs_raw_getpid",
        results=("oscalls-aarch64",),
    ),
    "the-os-layers-cost-call": Listing(
        symbol="sysfs_libc_getpid",
        results=("oscalls-aarch64",),
    ),
    "the-os-layers-cost-cost": Table(
        render=tables.os_cost_table,
        result="oscost-host",
    ),
    "the-os-layers-cost-faults": Table(
        render=tables.fault_cost_table,
        result="faultcost-host",
    ),
    "the-os-layers-cost-vdso": Table(
        render=tables.vdso_table,
        result="vdso-host",
    ),
    # -- ch27 ---------------------------------------------------------------------------
    "whole-machine-profiling-census": Table(
        render=tables.tally_census_table,
        result="tally-census",
    ),
    "whole-machine-profiling-sampling": Diagram(
        draw=sampling_profile,
        alt="A cycle counter overflowing into an interrupt, the PC written down, and the loop "
        "where the instruction blamed is not the instruction that waited.",
        result="profiling-aarch64",
    ),
    "whole-machine-profiling-scatter": Listing(
        symbol="sysfs_tally_scatter",
        results=("profiling-aarch64",),
    ),
    "whole-machine-profiling-profile": Table(
        render=tables.profile_table,
        result="profile-host",
    ),
    "whole-machine-profiling-skid": Table(
        render=tables.skid_table,
        result="skid-host",
    ),
    # -- ch28 ---------------------------------------------------------------------------
    "vectors-loops": Table(
        render=tables.vector_loops_table,
        result="vectors-census",
    ),
    "vectors-scale": Listing(
        symbol="sysfs_vec_scale",
        # The book's own level first, because that is what a reader building this code gets.
        results=("vectors-o2", "vectors-o3"),
    ),
    "vectors-sum-f32": Listing(
        symbol="sysfs_vec_sum_f32",
        # The refusal, then the same loop with permission to change the answer.
        results=("vectors-o3", "vectors-o3fast"),
    ),
    "vectors-running": Listing(
        symbol="sysfs_vec_running",
        results=("vectors-o3fast",),
    ),
    "vectors-speedup": Table(
        render=tables.vector_speedup_table,
        result="vectors-host",
    ),
    # -- ch02 ---------------------------------------------------------------------------
    "c-without-a-runtime-absences": Table(
        render=tables.kernel_absences_table,
        result="kernelc-xv6",
    ),
    "c-without-a-runtime-pools": Table(
        render=tables.kernel_pools_table,
        result="kernelc-xv6",
    ),
    # -- ch01 ---------------------------------------------------------------------------
    "memory-is-one-array-firstc": Table(
        render=tables.first_program_table,
        result="firstc",
    ),
    "memory-is-one-array-step-narrow": Listing(
        symbol="sysfs_step_narrow",
        results=("declarations-riscv64",),
    ),
    "memory-is-one-array-step-wide": Listing(
        symbol="sysfs_step_wide",
        results=("declarations-riscv64",),
    ),
    "memory-is-one-array-reach": Listing(
        symbol="sysfs_reach_through",
        results=("declarations-riscv64",),
    ),
    # -- appendix D ---------------------------------------------------------------------
    "appendix-d-map": Table(
        render=tables.xv6_file_map_table,
        result="filemap-xv6",
    ),
    "appendix-d-size": Table(
        render=tables.xv6_kernel_size_table,
        result="filemap-xv6",
    ),
    # -- Part II: the machine with nothing on it ----------------------------------------
    "a-trap-with-nothing-else-path": Diagram(
        draw=bare_trap,
        alt="What the hardware writes at a trap, and what it leaves untouched.",
        result="trap-bare",
    ),
    "a-trap-with-nothing-else-trap": Table(
        render=tables.bare_claims_table,
        result="trap-bare",
    ),
    "interrupts-and-privilege-path": Diagram(
        draw=privilege_path,
        alt="Machine mode drops to supervisor with mret, and a refused instruction traps it back.",
        result="privilege-bare",
    ),
    "interrupts-and-privilege-privilege": Table(
        render=tables.bare_claims_table,
        result="privilege-bare",
    ),
    "one-page-table-two-harts-alias": Diagram(
        draw=gigapage_alias,
        alt="Three gigapage entries: two identity mappings and one alias into RAM.",
        result="paging-bare",
    ),
    "one-page-table-two-harts-paging": Table(
        render=tables.bare_claims_table,
        result="paging-bare",
    ),
    "one-page-table-two-harts-harts": Table(
        render=tables.bare_claims_table,
        result="harts-bare",
    ),
    "a-system-call-of-your-own-syscall": Table(
        render=tables.bare_claims_table,
        result="syscall-bare",
    ),
    "a-small-integer-that-means-a-device-descriptors": Table(
        render=tables.bare_claims_table,
        result="descriptors-bare",
    ),
    "fork-built-rather-than-read-fork": Table(
        render=tables.bare_claims_table,
        result="fork-bare",
    ),
    # -- ch01 ---------------------------------------------------------------------------
    # One table, in the chapter that establishes it. Appendix H links here rather than declaring a
    # second figure from the same result: the renderer already carries both the identity rows and
    # the two capability rows, so a second id would render the same bytes under another name.
    "setting-up-the-board-report": Table(
        render=tables.board_identity_table,
        result="setup-host",
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
