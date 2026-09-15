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
    "bare": "runs under qemu-system-riscv64 with no operating system at all; answers questions "
    "about what the hardware does, and like `xv6` is never timed",
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
    #: two targets: Part V is not a second book, it is Part IV's chapters asked again as
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
    #: costs is exactly this field: a reader who learned RISC-V in Part III meets AArch64 in the
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


PART_START = "Getting started"
PART_C = "Part I — C, and what the machine does with it"
PART_BARE = "Part II — The machine with nothing on it"
PART_MACHINE = "Part III — What a computer does with a program"
PART_OS = "Part IV — The operating system layer"
PART_COST = "Part V — Where the cycles go"

CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        0,
        "prerequisites_and_setup",
        "Prerequisites and Setup",
        PART_START,
        "both",
        "What do I need on my desk, and how do I know it works?",
        "ch00-setup",
        reads_disassembly="both",
    ),
    Chapter(
        1,
        "reading_c",
        "Reading C",
        PART_C,
        "xv6",
        "How do I read a C declaration, and what does each piece of it become?",
        "ch01-reading-c",
        reads_disassembly="riscv",
        owes="What each construct compiles to: `p + 1` scaled by the element type, `->` as an "
        "offset on a load, and a struct's members at the addresses ch10 will explain.",
    ),
    Chapter(
        2,
        "c_without_a_runtime",
        "C Without a Runtime",
        PART_C,
        "xv6",
        "I already write C — which of my habits stop working in a kernel?",
        "ch02-no-runtime",
        owes="What the kernel does not have, counted from the kernel as built: its stack size, "
        "its floating-point instructions, and how much of the C library it reimplements.",
    ),
    Chapter(
        3,
        "c_for_people_who_will_read_a_kernel",
        "C for People Who Will Read a Kernel",
        PART_C,
        "xv6",
        "Which parts of C are really about addresses, and how do I read them without flinching?",
        "ch03-c",
        reads_disassembly="riscv",
        owes="The code the compiler emits for each construct — the disassembly is the evidence.",
    ),
    Chapter(
        4,
        "a_trap_with_nothing_else",
        "A Trap, With Nothing Else in the Machine",
        PART_BARE,
        "bare",
        "What is a trap, when nothing else is going on?",
        "ch04-bare-trap",
        owes="The whole of a trap in one program: where the handler was, where the interrupted "
        "instruction was, and that execution resumed after it.",
    ),
    Chapter(
        5,
        "interrupts_and_privilege",
        "Interrupts, and Who Is Allowed To",
        PART_BARE,
        "bare",
        "What arrives without being asked for, and what does a privilege level actually restrict?",
        "ch05-bare-interrupt",
        owes="A timer interrupt taken with no kernel present, and an access refused because the "
        "program had dropped a privilege level.",
    ),
    Chapter(
        6,
        "one_page_table_two_harts",
        "One Page Table, Two Harts",
        PART_BARE,
        "bare",
        "What does address translation do, and what does a second core break?",
        "ch06-bare-paging",
        owes="One mapping installed by hand and an address that means something else afterwards; "
        "and a counter two harts disagree about.",
    ),
    Chapter(
        7,
        "a_system_call_of_your_own",
        "A System Call of Your Own",
        PART_BARE,
        "bare",
        "What has to exist before `ecall` is a system call rather than a trap?",
        "ch07-bare-syscall",
        owes="A call number, arguments and a return value crossing the boundary, and the count of "
        "registers this handler has to save once the caller is a stranger.",
    ),
    Chapter(
        8,
        "fork_built_rather_than_read",
        "fork, Built Rather Than Read",
        PART_BARE,
        "bare",
        "What is the least a machine needs before two programs can run on it?",
        "ch08-bare-fork",
        owes="Two address spaces from one, a return value that differs between them, and the "
        "count of pages copied — beside what xv6 copies for the same call.",
    ),
    Chapter(
        9,
        "what_a_computer_does_with_a_program",
        "What a Computer Does With a Program",
        PART_MACHINE,
        "both",
        "What actually happens between a source file and a result, and which of it costs anything?",
        "ch09-whole-stack",
        reads_disassembly="riscv",
        owes="Object and section sizes at each toolchain stage (`xv6`), and instruction counts for "
        "the same program under `perf stat` (`host`).",
    ),
    Chapter(
        10,
        "representing_information",
        "Representing Information",
        PART_MACHINE,
        "xv6",
        "What is a number to this machine, and when does that answer bite?",
        "ch10-bits",
        reads_disassembly="riscv",
        owes="Type sizes, alignments and struct layouts, and what signed overflow and shifts "
        "actually compile to.",
    ),
    Chapter(
        11,
        "machine_level_code_on_riscv",
        "Machine-Level Code on RISC-V",
        PART_MACHINE,
        "xv6",
        "What did the compiler actually emit, and how do I read it?",
        "ch11-asm",
        reads_disassembly="riscv",
        owes="Instruction mix and frame sizes for a set of small functions at `-O0` and `-O2`. "
        "Static facts about emitted code, never timings.",
    ),
    Chapter(
        12,
        "linking_and_loading",
        "Linking and Loading",
        PART_MACHINE,
        "xv6",
        "How does a file on disk become an address space?",
        "ch12-elf",
        owes="Section and segment tables for xv6's own binaries, and what `exec` maps where.",
    ),
    Chapter(
        13,
        "traps_and_system_calls",
        "Traps and System Calls",
        PART_OS,
        "xv6",
        "What does the hardware do when a program asks the kernel for something?",
        "ch13-traps",
        owes="Instructions on the trap path, counted by instrumentation rather than timed, and the "
        "register and CSR state saved and restored.",
    ),
    Chapter(
        14,
        "virtual_memory",
        "Virtual Memory",
        PART_OS,
        "xv6",
        "What is an address, and who decides what it means?",
        "ch14-vm",
        owes="The page-table shape of a running process: levels, entries, and physical pages "
        "consumed per mapping.",
    ),
    Chapter(
        15,
        "page_faults_as_a_feature",
        "Page Faults as a Feature",
        PART_OS,
        "xv6",
        "What can a kernel do with a fault it expected?",
        "ch15-faults",
        owes="Fault counts and pages allocated for one workload, with each feature and without it.",
    ),
    Chapter(
        16,
        "interrupts_and_drivers",
        "Interrupts and Drivers",
        PART_OS,
        "xv6",
        "How does a device get the CPU's attention, and what does the CPU do about it?",
        "ch16-devices",
        owes="Interrupt counts by source over a defined workload, and buffer occupancy under load.",
    ),
    Chapter(
        17,
        "locks_and_memory_ordering",
        "Locks and Memory Ordering",
        PART_OS,
        "xv6",
        "What breaks when two harts touch the same memory, and what is the minimum fix?",
        "ch17-locks",
        owes="What a lock is made of, in instructions: the atomic that excludes, the fence that "
        "orders, and what turning interrupts off costs beside them.",
    ),
    Chapter(
        18,
        "scheduling_and_context_switches",
        "Scheduling and Context Switches",
        PART_OS,
        "xv6",
        "What exactly is saved, and what does it mean to say a thread 'runs'?",
        "ch18-sched",
        owes="Context switches per workload, bytes saved per switch, and the exact register set.",
    ),
    Chapter(
        19,
        "the_file_system",
        "The File System",
        PART_OS,
        "xv6",
        "What has to be true on the disk for a crash mid-write to be survivable?",
        "ch19-fs",
        owes="Block reads and writes for a traced operation, and the amplification between a "
        "one-byte write and the disk traffic it causes.",
    ),
    Chapter(
        20,
        "the_same_program_on_both_targets",
        "The Same Program on Both Targets",
        PART_OS,
        "both",
        "What does watching a program in a debugger fail to tell me about what it costs?",
        "ch20-bridge",
        answers=("ch11", "ch13", "ch14"),
        owes="The same structural facts from both targets, and the first side-by-side timing: the "
        "board's, against QEMU's meaningless equivalent, shown deliberately.",
    ),
    Chapter(
        21,
        "measuring",
        "Measuring",
        PART_COST,
        "host",
        "How do I get a number I would defend, and how would I know it was wrong?",
        "ch21-measuring",
        owes="Clock resolution and read cost; one fixed workload's distribution over many "
        "repetitions; the same benchmark made to give three answers by changing what should "
        "not matter.",
    ),
    Chapter(
        22,
        "the_memory_hierarchy",
        "The Memory Hierarchy",
        PART_COST,
        "host",
        "Where is the data, and what does each extra step out cost?",
        "ch22-memory",
        answers=("ch10", "ch14"),
        assumes="a particular cache hierarchy — the levels, sizes, line size and TLB reach "
        "are this core's. The method transfers to any machine; the numbers do not, and "
        "measuring your own is the exercise.",
        owes="Latency against working-set size and against stride; measured cache and line sizes "
        "against the vendor's figures; TLB reach.",
    ),
    Chapter(
        23,
        "optimising_code",
        "Optimising Code",
        PART_COST,
        "host",
        "What will the compiler do for me, and what will it never do?",
        "ch23-optimising",
        answers=("ch11",),
        reads_disassembly="aarch64",
        owes="Each transformation at `-O0`, `-O2` and `-O3` with the disassembly that explains it, "
        "including one where the optimisation does nothing because the compiler had already "
        "done it.",
    ),
    Chapter(
        24,
        "the_cpu",
        "The CPU",
        PART_COST,
        "host",
        "What is this core doing between fetching an instruction and finishing it?",
        "ch24-cpu",
        answers=("ch11",),
        reads_disassembly="aarch64",
        assumes="a specific microarchitecture. The reference is an out-of-order, 4-wide "
        "Cortex-A76; core width, branch predictor and PMU event names all differ elsewhere, "
        "and on an in-order core these experiments get easier to read, not harder.",
        owes="Misprediction rate against branch predictability; IPC against dependency-chain "
        "length; the cost of a mispredict, derived and stated as derived.",
    ),
    Chapter(
        25,
        "memory_ordering_on_real_hardware",
        "Memory Ordering on Real Hardware",
        PART_COST,
        "host",
        "What do four cores cost each other, and what does a fence actually buy?",
        "ch25-concurrency",
        answers=("ch17",),
        assumes="four cores, and this interconnect's coherence behaviour. A different core "
        "count moves the scaling curve without changing the mechanism; two cores make the "
        "chapter thin.",
        owes="Throughput against sharing distance; atomic cost, contended and uncontended; fence "
        "cost; scaling from one core to four.",
    ),
    Chapter(
        26,
        "the_os_layers_cost",
        "The OS Layer's Cost on Real Hardware",
        PART_COST,
        "host",
        "What does Linux charge for the services xv6 showed me?",
        "ch26-os-cost",
        answers=("ch13", "ch15", "ch18"),
        owes="The cost of a system call, a fault and a switch, each beside the cheapest available "
        "baseline; a minor fault against a major one; `vDSO` against a real trap.",
    ),
    Chapter(
        27,
        "whole_machine_profiling",
        "Whole-Machine Profiling",
        PART_COST,
        "host",
        "How do I find the bottleneck in something I did not write?",
        "ch27-profiling",
        assumes="that perf can sample. ARM PMUs support counter-overflow interrupts as "
        "standard, so this works on the reference machine — but most affordable RISC-V cores "
        "do not, and a reader following Part V on one will find this the chapter they "
        "cannot run.",
        owes="Profiles of the supplied program before and after, and a sampling artefact shown "
        "deliberately.",
    ),
    Chapter(
        28,
        "vectors",
        "Vectors",
        PART_COST,
        "host",
        "What does vectorising actually buy, and when will the compiler do it for me?",
        "ch28-vectors",
        reads_disassembly="aarch64",
        assumes="a vector unit — NEON on the reference core. This chapter became measurable "
        "when Part V moved to AArch64; on a RISC-V board without RVV 1.0 it reverts to "
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
        "to Part IV, and the page to keep open while reading [ch13](#ch13) onwards.",
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
        "fences — each beside its RISC-V equivalent from Part III.",
        source="A translation, not a reference. Written for someone who has read [ch11](#ch11) "
        "and is about to read [ch23](#ch23), and organised as *you know this already, here it "
        "is again*. It takes its shape from ch23, so it is drafted after it.",
    ),
    Appendix(
        "G",
        "reading_xv6",
        "Reading xv6 Alongside This Book",
        holds="Which of this book's chapters covers the ground of which part of the xv6 "
        "commentary, and one system call traced through every layer it touches.",
        source="The submodule at its pinned commit, read rather than recalled, so the trace "
        "describes the code the reader has checked out. The commentary is named as a companion "
        "and is never a source.",
    ),
)

PARTS: tuple[str, ...] = (
    PART_START,
    PART_C,
    PART_BARE,
    PART_MACHINE,
    PART_OS,
    PART_COST,
)


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
