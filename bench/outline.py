"""The book's shape, in one machine-readable place.

PLAN.md holds the argument — what each chapter is for, what it must measure, what code it
leaves behind. This module holds only the facts a script or a test needs: the number, the title,
the part it belongs to, the target it runs on, and the checkpoint tag it earns.

Keeping them separate is deliberate. Prose that tries to be a data structure goes stale silently;
a data structure that tries to be prose stops being readable. ``tests/test_book.py`` ties the two
together by checking that every chapter here is described in PLAN.md, appears in ``myst.yml``'s
table of contents, exists on disk, and declares in its own header the target named here.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The two execution targets, and what it means for a chapter to declare one.
TARGET_MEANING = {
    "xv6": "runs on the xv6 teaching kernel under QEMU; answers questions about structure",
    "host": "runs natively on real hardware; the only place a timing may be measured",
    "both": "uses both targets, and says which one every example and figure came from",
}


@dataclass(frozen=True)
class Chapter:
    number: int
    slug: str
    title: str
    part: str
    target: str
    #: The one question the chapter answers. Its opening paragraph is an expansion of this.
    question: str
    #: Checkpoint tag, or None for a chapter that leaves no code behind (CHECKPOINTS.md).
    tag: str | None = None
    #: Earlier chapters whose *cost* this one measures. The spine across the seam between the
    #: two targets: Part III is not a second book, it is Part II's chapters asked again as
    #: questions about time. A chapter that names its counterpart is a chapter the reader
    #: arrives at already knowing the mechanism, needing only the price.
    #:
    #: Rendered as an "Answers the cost of" row in the chapter header, and checked by
    #: ``tests/test_book.py`` — a label here must be a real chapter, and it must come earlier.
    answers: tuple[str, ...] = ()
    #: The measurements this chapter must produce before it can lose its ``[DRAFT]`` marker,
    #: in one line. PLAN.md §4 has the full statement; this is the version a reader sees.
    #:
    #: It exists because the preface promises that every stub carries "its target, its question
    #: and the measurements it owes you", and for a while that was two-thirds true — the header
    #: row said *[To write: the figure this chapter produces]*, which tells a reader nothing and
    #: an author only what they already knew. A stub that names its debt is a table of contents
    #: for work not yet done; one that names a placeholder is twenty-one identical pages.
    owes: str | None = None
    #: Which instruction set's disassembly this chapter asks the reader to read, or None.
    #:
    #: The two targets do not share an instruction set, and the honest accounting of what that
    #: costs is exactly this field: a reader who learned RISC-V in Part I meets AArch64 in the
    #: chapters marked ``aarch64`` and nowhere else. The claim is load-bearing — it is the reason
    #: the split is affordable — so it is a fact here rather than a sentence three pages repeat
    #: and then disagree about, which is what happened before this existed.
    reads_disassembly: str | None = None
    #: What this chapter assumes about the *reference* machine, for chapters whose reading
    #: changes on different hardware. None means the chapter is hardware-neutral.
    #:
    #: ch00 states the hardware requirement as a capability rather than a part number, so a
    #: reader's board will differ from the one the committed figures came from. Most chapters do
    #: not care. These do, and saying so in their own header is what stops it being a surprise
    #: three hundred pages in — or being quietly dropped when the chapter is finally drafted.
    assumes: str | None = None

    @property
    def label(self) -> str:
        return f"ch{self.number:02d}"

    @property
    def path(self) -> str:
        return f"chapters/{self.label}_{self.slug}.md"


PART_I = "Part I — Foundations"
PART_II = "Part II — The operating system layer"
PART_III = "Part III — Where the cycles go"

CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        0,
        "prerequisites_and_setup",
        "Prerequisites and Setup",
        PART_I,
        "both",
        "What do I need on my desk, and how do I know it works?",
        "ch00-setup",
        reads_disassembly="both",
    ),
    Chapter(
        1,
        "what_a_computer_does_with_a_program",
        "What a Computer Does With a Program",
        PART_I,
        "both",
        "What actually happens between a source file and a result, and which of it costs anything?",
        "ch01-whole-stack",
        owes="Object and section sizes at each toolchain stage (`xv6`), and instruction counts for "
        "the same program under `perf stat` (`host`).",
    ),
    Chapter(
        2,
        "representing_information",
        "Representing Information",
        PART_I,
        "xv6",
        "What is a number to this machine, and when does that answer bite?",
        "ch02-bits",
        owes="Type sizes, alignments and struct layouts, and what signed overflow and shifts "
        "actually compile to.",
    ),
    Chapter(
        3,
        "c_for_people_who_will_read_a_kernel",
        "C for People Who Will Read a Kernel",
        PART_I,
        "xv6",
        "Which parts of C are really about addresses, and how do I read them without flinching?",
        "ch03-c",
        reads_disassembly="riscv",
        owes="The code the compiler emits for each construct — the disassembly is the evidence.",
    ),
    Chapter(
        4,
        "machine_level_code_on_riscv",
        "Machine-Level Code on RISC-V",
        PART_I,
        "xv6",
        "What did the compiler actually emit, and how do I read it?",
        "ch04-asm",
        reads_disassembly="riscv",
        owes="Instruction mix and frame sizes for a set of small functions at `-O0` and `-O2`. "
        "Static facts about emitted code, never timings.",
    ),
    Chapter(
        5,
        "linking_and_loading",
        "Linking and Loading",
        PART_I,
        "xv6",
        "How does a file on disk become an address space?",
        "ch05-elf",
        owes="Section and segment tables for xv6's own binaries, and what `exec` maps where.",
    ),
    Chapter(
        6,
        "traps_and_system_calls",
        "Traps and System Calls",
        PART_II,
        "xv6",
        "What does the hardware do when a program asks the kernel for something?",
        "ch06-traps",
        owes="Instructions on the trap path, counted by instrumentation rather than timed, and the "
        "register and CSR state saved and restored.",
    ),
    Chapter(
        7,
        "virtual_memory",
        "Virtual Memory",
        PART_II,
        "xv6",
        "What is an address, and who decides what it means?",
        "ch07-vm",
        owes="The page-table shape of a running process: levels, entries, and physical pages "
        "consumed per mapping.",
    ),
    Chapter(
        8,
        "page_faults_as_a_feature",
        "Page Faults as a Feature",
        PART_II,
        "xv6",
        "What can a kernel do with a fault it expected?",
        "ch08-faults",
        owes="Fault counts and pages allocated for one workload, with each feature and without it.",
    ),
    Chapter(
        9,
        "interrupts_and_drivers",
        "Interrupts and Drivers",
        PART_II,
        "xv6",
        "How does a device get the CPU's attention, and what does the CPU do about it?",
        "ch09-devices",
        owes="Interrupt counts by source over a defined workload, and buffer occupancy under load.",
    ),
    Chapter(
        10,
        "locks_and_memory_ordering",
        "Locks and Memory Ordering",
        PART_II,
        "xv6",
        "What breaks when two harts touch the same memory, and what is the minimum fix?",
        "ch10-locks",
        owes="Acquisitions and contentions per lock, and the interleavings that break an unlocked "
        "counter — deterministic under QEMU, which is the one thing emulation makes easier.",
    ),
    Chapter(
        11,
        "scheduling_and_context_switches",
        "Scheduling and Context Switches",
        PART_II,
        "xv6",
        "What exactly is saved, and what does it mean to say a thread 'runs'?",
        "ch11-sched",
        owes="Context switches per workload, bytes saved per switch, and the exact register set.",
    ),
    Chapter(
        12,
        "the_file_system",
        "The File System",
        PART_II,
        "xv6",
        "What has to be true on the disk for a crash mid-write to be survivable?",
        "ch12-fs",
        owes="Block reads and writes for a traced operation, and the amplification between a "
        "one-byte write and the disk traffic it causes.",
    ),
    Chapter(
        13,
        "the_same_program_on_both_targets",
        "The Same Program on Both Targets",
        PART_II,
        "both",
        "What does watching a program in a debugger fail to tell me about what it costs?",
        "ch13-bridge",
        answers=("ch04", "ch06", "ch07"),
        owes="The same structural facts from both targets, and the first side-by-side timing: the "
        "board's, against QEMU's meaningless equivalent, shown deliberately.",
    ),
    Chapter(
        14,
        "measuring",
        "Measuring",
        PART_III,
        "host",
        "How do I get a number I would defend, and how would I know it was wrong?",
        "ch14-measuring",
        owes="Clock resolution and read cost; one fixed workload's distribution over many "
        "repetitions; the same benchmark made to give three answers by changing what should "
        "not matter.",
    ),
    Chapter(
        15,
        "the_memory_hierarchy",
        "The Memory Hierarchy",
        PART_III,
        "host",
        "Where is the data, and what does each extra step out cost?",
        "ch15-memory",
        answers=("ch02", "ch07"),
        assumes="a particular cache hierarchy — the levels, sizes, line size and TLB reach "
        "are this core's. The method transfers to any machine; the numbers do not, and "
        "measuring your own is the exercise.",
        owes="Latency against working-set size and against stride; measured cache and line sizes "
        "against the vendor's figures; TLB reach.",
    ),
    Chapter(
        16,
        "optimising_code",
        "Optimising Code",
        PART_III,
        "host",
        "What will the compiler do for me, and what will it never do?",
        "ch16-optimising",
        answers=("ch04",),
        reads_disassembly="aarch64",
        owes="Each transformation at `-O0`, `-O2` and `-O3` with the disassembly that explains it, "
        "including one where the optimisation does nothing because the compiler had already "
        "done it.",
    ),
    Chapter(
        17,
        "the_cpu",
        "The CPU",
        PART_III,
        "host",
        "What is this core doing between fetching an instruction and finishing it?",
        "ch17-cpu",
        answers=("ch04",),
        reads_disassembly="aarch64",
        assumes="a specific microarchitecture. The reference is an out-of-order, 4-wide "
        "Cortex-A76; core width, branch predictor and PMU event names all differ elsewhere, "
        "and on an in-order core these experiments get easier to read, not harder.",
        owes="Misprediction rate against branch predictability; IPC against dependency-chain "
        "length; the cost of a mispredict, derived and stated as derived.",
    ),
    Chapter(
        18,
        "memory_ordering_on_real_hardware",
        "Memory Ordering on Real Hardware",
        PART_III,
        "host",
        "What do four cores cost each other, and what does a fence actually buy?",
        "ch18-concurrency",
        answers=("ch10",),
        assumes="four cores, and this interconnect's coherence behaviour. A different core "
        "count moves the scaling curve without changing the mechanism; two cores make the "
        "chapter thin.",
        owes="Throughput against sharing distance; atomic cost, contended and uncontended; fence "
        "cost; scaling from one core to four.",
    ),
    Chapter(
        19,
        "the_os_layers_cost",
        "The OS Layer's Cost on Real Hardware",
        PART_III,
        "host",
        "What does Linux charge for the services xv6 showed me?",
        "ch19-os-cost",
        answers=("ch06", "ch08", "ch11"),
        owes="The cost of a system call, a fault and a switch, each beside the cheapest available "
        "baseline; a minor fault against a major one; `vDSO` against a real trap.",
    ),
    Chapter(
        20,
        "whole_machine_profiling",
        "Whole-Machine Profiling",
        PART_III,
        "host",
        "How do I find the bottleneck in something I did not write?",
        "ch20-profiling",
        assumes="that perf can sample. ARM PMUs support counter-overflow interrupts as "
        "standard, so this works on the reference machine — but most affordable RISC-V cores "
        "do not, and a reader following Part III on one will find this the chapter they "
        "cannot run.",
        owes="Profiles of the supplied program before and after, and a sampling artefact shown "
        "deliberately.",
    ),
    Chapter(
        21,
        "vectors",
        "Vectors",
        PART_III,
        "host",
        "What does vectorising actually buy, and when will the compiler do it for me?",
        "ch21-vectors",
        reads_disassembly="aarch64",
        assumes="a vector unit — NEON on the reference core. This chapter became measurable "
        "when Part III moved to AArch64; on a RISC-V board without RVV 1.0 it reverts to "
        "reasoning about code the compiler emits but the hardware cannot run.",
        owes="Speedup per loop with and without vectorisation, the emitted code that explains "
        "each, and one loop the compiler refuses — measured against the arithmetic bound, not "
        "celebrated alone.",
    ),
)


@dataclass(frozen=True)
class Appendix:
    """A reference section: no argument, no narrative, and a stated source for everything in it.

    ``holds`` and ``source`` exist for the same reason :attr:`Chapter.owes` does. Six appendix
    stubs that all said "[To write: an appendix is a reference, not a chapter]" were six identical
    pages, and a reader clicking Appendix F to find out what AArch64 help was coming learned
    nothing. Where each appendix's content will *come from* differs more than the titles suggest —
    a specification, the board itself, the submodule — and that is the part worth saying early,
    because it is what decides when the appendix can be written at all.
    """

    letter: str
    slug: str
    title: str
    #: What the finished appendix contains, in one line.
    holds: str = ""
    #: Where its content comes from, and therefore what has to happen before it can be written.
    source: str = ""

    @property
    def label(self) -> str:
        return f"appendix-{self.letter.lower()}"

    @property
    def path(self) -> str:
        return f"appendices/appendix_{self.letter.lower()}_{self.slug}.md"


APPENDICES: tuple[Appendix, ...] = (
    Appendix(
        "A",
        "riscv_reference",
        "RISC-V Registers and CSRs",
        holds="The register roles and the CSRs this book touches, with what each one does and "
        "the chapter that uses it.",
        source="The unprivileged and privileged specifications, redrawn rather than reproduced. "
        "Can be written as soon as the chapters that need it are.",
    ),
    Appendix(
        "B",
        "gdb_reference",
        "gdb for Kernels and RISC-V",
        holds="Attaching to QEMU, the xv6 workflow, watchpoints on physical memory, and what to "
        "do when the stack is nonsense.",
        source="Procedures verified against the repository's own `make xv6-gdb`, so every "
        "sequence here is one that has been run. [ch00](#ch00) sets the debugger up; this is "
        "where the workflow lives.",
    ),
    Appendix(
        "C",
        "perf_events",
        "The perf Events This Board Has",
        holds="Which events this machine exposes, which are hardware and which are derived.",
        source="Generated from the reference machine rather than written. **This is the one "
        "appendix that cannot be drafted from a desk**: it is a property of the silicon, the "
        "kernel and the firmware together, so it waits for `make bench-board`.",
    ),
    Appendix(
        "D",
        "xv6_file_map",
        "An xv6 File Map",
        holds="What lives in which file of the kernel, and which chapter reads it. The companion "
        "to Part II, and the page to keep open while reading [ch06](#ch06) onwards.",
        source="The submodule at its pinned commit, so the map describes the tree a reader "
        "actually has rather than a version of xv6 from a paper.",
    ),
    Appendix(
        "E",
        "glossary",
        "Glossary",
        holds="Terms, each with the chapter that defines it.",
        source="The chapters themselves. It is written last, because a glossary assembled before "
        "the prose defines the terms the prose did not end up using.",
    ),
    Appendix(
        "F",
        "aarch64_for_riscv_readers",
        "AArch64 for RISC-V Readers",
        holds="Registers and calling convention, the load/store and branch forms, atomics and "
        "fences — each beside its RISC-V equivalent from Part I.",
        source="A translation, not a reference. Written for someone who has read [ch04](#ch04) "
        "and is about to read [ch16](#ch16), and organised as *you know this already, here it "
        "is again*. It takes its shape from ch16, so it is drafted after it.",
    ),
)

PARTS: tuple[str, ...] = (PART_I, PART_II, PART_III)


def reading_disassembly(instruction_set: str) -> tuple[str, ...]:
    """Which chapters ask the reader to read this instruction set's disassembly.

    The cost of the two targets not sharing an instruction set is exactly the ``aarch64`` answer,
    which is why three separate pages state it and why it now has one source. They had already
    drifted into naming three different sets before this existed.
    """
    return tuple(
        chapter.label
        for chapter in CHAPTERS
        if chapter.reads_disassembly in (instruction_set, "both")
    )


def by_number(number: int) -> Chapter:
    for chapter in CHAPTERS:
        if chapter.number == number:
            return chapter
    raise KeyError(f"no chapter {number}")


def in_part(part: str) -> list[Chapter]:
    return [chapter for chapter in CHAPTERS if chapter.part == part]
