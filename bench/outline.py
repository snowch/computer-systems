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

#: The three execution targets, and what it means for a chapter to declare one.
TARGET_MEANING = {
    "xv6": "runs on the xv6 teaching kernel under QEMU; answers questions about structure",
    "host": "runs natively on real hardware; the only place a timing may be measured",
    "bare": "runs under qemu-system-riscv64 with no operating system at all; answers questions "
    "about what the hardware does, and like `xv6` is never timed",
    "both": "uses the `xv6` and `host` targets together, and says which one every example "
    "and figure came from",
}

#: Which machine each target needs. Three targets, but only two machines: `bare` and `xv6` are
#: both QEMU on whatever you are working on, so they share a cross compiler and a single set of
#: checks in `scripts/verify-setup.py`. Only `host` has to be real hardware. The preface states
#: both counts and `tests/test_book.py` derives them from here, because the first of them was
#: wrong on that page for as long as Part II had existed.
TARGET_MACHINE = {
    "bare": "the computer you are working on, under QEMU",
    "xv6": "the computer you are working on, under QEMU",
    "host": "a Linux board with working performance counters",
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
    def anchor(self) -> str:
        """The chapter's identity: its title, and never its position.

        Everything that has to survive a chapter being inserted uses this — the MyST label, the
        file on disk, the directory its problems live in, its checkpoint tag, the ids of the
        figures it owns, and the URL a reader bookmarks.

        The number is deliberately absent. It is a statement about where the chapter currently
        sits, and this book has already moved it three times: Part I was added in front of
        everything, then Part II, then a chapter inside Part II. Each of those renamed every
        identifier downstream of it, broke cross-references that ``--strict`` could see and prose
        that it could not, and invalidated every permalink to the published site.

        That is the same failure the book already refuses everywhere else. A chapter number is a
        number, it goes stale, and the rule here is the rule for every other number: derive it,
        never type it. :attr:`label` is the derived form, and ``scripts/sync-labels.py`` keeps the
        typed-looking ones in prose honest.
        """
        return self.slug.replace("_", "-")

    @property
    def label(self) -> str:
        """``ch17`` — how prose refers to the chapter. Derived from position, never an identifier.

        The ``ch`` earns its place in a sentence: ``[17]`` in a paragraph with other numbers in it
        reads as a quantity rather than a destination. It earns nothing in a heading or a sidebar
        entry, where there is nothing else a number beside a chapter title could mean, so those
        use :attr:`display` instead.
        """
        return f"ch{self.number:02d}"

    @property
    def display(self) -> str:
        """``17`` — the heading and sidebar form, where the context is already a list of chapters."""
        return f"{self.number:02d}"

    @property
    def path(self) -> str:
        return f"chapters/{self.slug}.md"

    @property
    def tests_dir(self) -> str:
        return f"tests/{self.slug}"

    def figure(self, name: str) -> str:
        """The id of a figure this chapter owns, e.g. ``memory-is-one-array-firstc``."""
        return f"{self.anchor}-{name}"


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
        "prerequisites-and-setup",
        reads_disassembly="both",
    ),
    Chapter(
        1,
        "memory_is_one_array",
        "Memory Is One Array",
        PART_C,
        "xv6",
        "If memory is one array of bytes, what is a C declaration saying about it?",
        "memory-is-one-array",
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
        "c-without-a-runtime",
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
        "c-for-people-who-will-read-a-kernel",
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
        "a-trap-with-nothing-else",
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
        "interrupts-and-privilege",
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
        "one-page-table-two-harts",
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
        "a-system-call-of-your-own",
        owes="A call number, arguments and a return value crossing the boundary, and the count of "
        "registers this handler has to save once the caller is a stranger.",
    ),
    Chapter(
        8,
        "a_small_integer_that_means_a_device",
        "A Small Integer That Means a Device",
        PART_BARE,
        "bare",
        "Why does a program name what it reads by number, and what does that number find?",
        "a-small-integer-that-means-a-device",
        owes="One `write` call reaching two unrelated destinations through one table, and the "
        "table itself printed before and after a descriptor is duplicated.",
    ),
    Chapter(
        9,
        "fork_built_rather_than_read",
        "fork, Built Rather Than Read",
        PART_BARE,
        "bare",
        "What is the least a machine needs before two programs can run on it?",
        "fork-built-rather-than-read",
        owes="Two address spaces from one, a return value that differs between them, and the count "
        "of pages copied — beside what xv6 copies for the same call.",
    ),
    Chapter(
        10,
        "what_a_computer_does_with_a_program",
        "What a Computer Does With a Program",
        PART_MACHINE,
        "both",
        "What actually happens between a source file and a result, and which of it costs anything?",
        "what-a-computer-does-with-a-program",
        reads_disassembly="riscv",
        owes="Object and section sizes at each toolchain stage (`xv6`), and instruction counts for "
        "the same program under `perf stat` (`host`).",
    ),
    Chapter(
        11,
        "representing_information",
        "Representing Information",
        PART_MACHINE,
        "xv6",
        "What is a number to this machine, and when does that answer bite?",
        "representing-information",
        reads_disassembly="riscv",
        owes="Type sizes, alignments and struct layouts, and what signed overflow and shifts "
        "actually compile to.",
    ),
    Chapter(
        12,
        "machine_level_code_on_riscv",
        "Machine-Level Code on RISC-V",
        PART_MACHINE,
        "xv6",
        "What did the compiler actually emit, and how do I read it?",
        "machine-level-code-on-riscv",
        reads_disassembly="riscv",
        owes="Instruction mix and frame sizes for a set of small functions at `-O0` and `-O2`. "
        "Static facts about emitted code, never timings.",
    ),
    Chapter(
        13,
        "linking_and_loading",
        "Linking and Loading",
        PART_MACHINE,
        "xv6",
        "How does a file on disk become an address space?",
        "linking-and-loading",
        owes="Section and segment tables for xv6's own binaries, and what `exec` maps where.",
    ),
    Chapter(
        14,
        "traps_and_system_calls",
        "Traps and System Calls",
        PART_OS,
        "xv6",
        "What does the hardware do when a program asks the kernel for something?",
        "traps-and-system-calls",
        owes="Instructions on the trap path, counted by instrumentation rather than timed, and the "
        "register and CSR state saved and restored.",
    ),
    Chapter(
        15,
        "virtual_memory",
        "Virtual Memory",
        PART_OS,
        "xv6",
        "What is an address, and who decides what it means?",
        "virtual-memory",
        owes="The page-table shape of a running process: levels, entries, and physical pages "
        "consumed per mapping.",
    ),
    Chapter(
        16,
        "page_faults_as_a_feature",
        "Page Faults as a Feature",
        PART_OS,
        "xv6",
        "What can a kernel do with a fault it expected?",
        "page-faults-as-a-feature",
        owes="Fault counts and pages allocated for one workload, with each feature and without it.",
    ),
    Chapter(
        17,
        "interrupts_and_drivers",
        "Interrupts and Drivers",
        PART_OS,
        "xv6",
        "How does a device get the CPU's attention, and what does the CPU do about it?",
        "interrupts-and-drivers",
        owes="Interrupt counts by source over a defined workload, and buffer occupancy under load.",
    ),
    Chapter(
        18,
        "locks_and_memory_ordering",
        "Locks and Memory Ordering",
        PART_OS,
        "xv6",
        "What breaks when two harts touch the same memory, and what is the minimum fix?",
        "locks-and-memory-ordering",
        owes="What a lock is made of, in instructions: the atomic that excludes, the fence that "
        "orders, and what turning interrupts off costs beside them.",
    ),
    Chapter(
        19,
        "scheduling_and_context_switches",
        "Scheduling and Context Switches",
        PART_OS,
        "xv6",
        "What exactly is saved, and what does it mean to say a thread 'runs'?",
        "scheduling-and-context-switches",
        owes="Context switches per workload, bytes saved per switch, and the exact register set.",
    ),
    Chapter(
        20,
        "the_file_system",
        "The File System",
        PART_OS,
        "xv6",
        "What has to be true on the disk for a crash mid-write to be survivable?",
        "the-file-system",
        owes="Block reads and writes for a traced operation, and the amplification between a "
        "one-byte write and the disk traffic it causes.",
    ),
    Chapter(
        21,
        "the_same_program_on_both_targets",
        "The Same Program on Both Targets",
        PART_OS,
        "both",
        "What does watching a program in a debugger fail to tell me about what it costs?",
        "the-same-program-on-both-targets",
        answers=("machine-level-code-on-riscv", "traps-and-system-calls", "virtual-memory"),
        owes="The same structural facts from both targets, and the first side-by-side timing: the "
        "board's, against QEMU's meaningless equivalent, shown deliberately.",
    ),
    Chapter(
        22,
        "measuring",
        "Measuring",
        PART_COST,
        "host",
        "How do I get a number I would defend, and how would I know it was wrong?",
        "measuring",
        owes="Clock resolution and read cost; one fixed workload's distribution over many "
        "repetitions; the same benchmark made to give three answers by changing what should "
        "not matter.",
    ),
    Chapter(
        23,
        "the_memory_hierarchy",
        "The Memory Hierarchy",
        PART_COST,
        "host",
        "Where is the data, and what does each extra step out cost?",
        "the-memory-hierarchy",
        answers=("representing-information", "virtual-memory"),
        assumes="a particular cache hierarchy — the levels, sizes, line size and TLB reach "
        "are this core's. The method transfers to any machine; the numbers do not, and "
        "measuring your own is the exercise.",
        owes="Latency against working-set size and against stride; measured cache and line sizes "
        "against the vendor's figures; TLB reach.",
    ),
    Chapter(
        24,
        "optimising_code",
        "Optimising Code",
        PART_COST,
        "host",
        "What will the compiler do for me, and what will it never do?",
        "optimising-code",
        answers=("machine-level-code-on-riscv",),
        reads_disassembly="aarch64",
        owes="Each transformation at `-O0`, `-O2` and `-O3` with the disassembly that explains it, "
        "including one where the optimisation does nothing because the compiler had already "
        "done it.",
    ),
    Chapter(
        25,
        "the_cpu",
        "The CPU",
        PART_COST,
        "host",
        "What is this core doing between fetching an instruction and finishing it?",
        "the-cpu",
        answers=("machine-level-code-on-riscv",),
        reads_disassembly="aarch64",
        assumes="a specific microarchitecture. The reference is an out-of-order, 4-wide "
        "Cortex-A76; core width, branch predictor and PMU event names all differ elsewhere, "
        "and on an in-order core these experiments get easier to read, not harder.",
        owes="Misprediction rate against branch predictability; IPC against dependency-chain "
        "length; the cost of a mispredict, derived and stated as derived.",
    ),
    Chapter(
        26,
        "memory_ordering_on_real_hardware",
        "Memory Ordering on Real Hardware",
        PART_COST,
        "host",
        "What do four cores cost each other, and what does a fence actually buy?",
        "memory-ordering-on-real-hardware",
        answers=("locks-and-memory-ordering",),
        assumes="four cores, and this interconnect's coherence behaviour. A different core "
        "count moves the scaling curve without changing the mechanism; two cores make the "
        "chapter thin.",
        owes="Throughput against sharing distance; atomic cost, contended and uncontended; fence "
        "cost; scaling from one core to four.",
    ),
    Chapter(
        27,
        "the_os_layers_cost",
        "The OS Layer's Cost on Real Hardware",
        PART_COST,
        "host",
        "What does Linux charge for the services xv6 showed me?",
        "the-os-layers-cost",
        answers=(
            "traps-and-system-calls",
            "page-faults-as-a-feature",
            "scheduling-and-context-switches",
        ),
        owes="The cost of a system call, a fault and a switch, each beside the cheapest available "
        "baseline; a minor fault against a major one; `vDSO` against a real trap.",
    ),
    Chapter(
        28,
        "whole_machine_profiling",
        "Whole-Machine Profiling",
        PART_COST,
        "host",
        "How do I find the bottleneck in something I did not write?",
        "whole-machine-profiling",
        assumes="that perf can sample. ARM PMUs support counter-overflow interrupts as "
        "standard, so this works on the reference machine — but most affordable RISC-V cores "
        "do not, and a reader following Part V on one will find this the chapter they "
        "cannot run.",
        owes="Profiles of the supplied program before and after, and a sampling artefact shown "
        "deliberately.",
    ),
    Chapter(
        29,
        "vectors",
        "Vectors",
        PART_COST,
        "host",
        "What does vectorising actually buy, and when will the compiler do it for me?",
        "vectors",
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
        "sequence here is one that has been run. [ch00](#prerequisites-and-setup) sets the debugger up; this is "
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
        "to Part IV, and the page to keep open while reading [ch13](#traps-and-system-calls) onwards.",
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
        source="A translation, not a reference. Written for someone who has read [ch11](#machine-level-code-on-riscv) "
        "and is about to read [ch23](#optimising-code), and organised as *you know this already, here it "
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


@dataclass(frozen=True)
class Part:
    """A part of the book, and the page that says what it is for.

    Parts were unclickable sidebar labels for a long time: ``myst.yml`` gave each one a ``title``
    and a list of children and no page of its own, so the only statement of what a part was for
    lived in one hand-maintained row of the preface table — which is exactly where Part II went
    missing for a while without any check noticing, because ``myst build --strict`` verifies that
    an anchor resolves and not that the words around it are true.

    What that arrangement could not hold is anything part-shaped. Part I's routing note — *if you
    already write C, skip to ch02* — sat inside ch01, so a reader who took its advice only ever
    saw it by accident. Part V's dependence on the reference machine was stated five times, once
    per chapter header, with nowhere to say it properly. A part page is where those go.

    The content rule is narrow on purpose: **a part page states a claim and a boundary, and never
    summarises its chapters.** The chapter list is already in the sidebar and in the preface, and
    a page that repeats it is the "in this part we will" filler CLAUDE.md §7 bans.
    """

    #: 1-5, matching the Roman numeral in :attr:`title`. ``0`` is *Getting started*, which is a
    #: part in the table of contents but has no page: it holds one chapter, and the preface
    #: already does the job a part page would.
    number: int
    slug: str
    title: str
    #: The target its chapters run on, in the vocabulary of :data:`TARGET_MEANING`. A part-level
    #: fact rather than a per-chapter one — Part II is ``bare`` throughout, and the rule that
    #: nothing in it may be timed is the part's rule, not five separate chapters' rules.
    target: str
    #: What the part asserts, in one line. Mirrors :attr:`Chapter.question`: prose kept in the
    #: data so a stub can state it and a test can find it, rather than being invented afresh on
    #: the page and drifting from the preface's description of the same part.
    claim: str
    #: False only for *Getting started*.
    page: bool = True

    @property
    def label(self) -> str:
        return f"part{self.number}"

    @property
    def path(self) -> str:
        return f"chapters/{self.label}_{self.slug}.md"

    @property
    def name(self) -> str:
        """``"Part III"`` — the title without its subtitle."""
        return self.title.split(" \u2014 ")[0]

    @property
    def subtitle(self) -> str:
        """``"What a computer does with a program"`` — the title without its number."""
        return self.title.split(" \u2014 ", 1)[-1]


PARTS: tuple[Part, ...] = (
    Part(
        0,
        "getting_started",
        PART_START,
        "both",
        "Two targets working, and a script that says what this machine can currently run.",
        page=False,
    ),
    Part(
        1,
        "c_and_the_machine",
        PART_C,
        "xv6",
        "Enough C to read a kernel and change it, and no more.",
    ),
    Part(
        2,
        "the_bare_machine",
        PART_BARE,
        "bare",
        "Each primitive of the machine built on its own, before a kernel presents them entangled.",
    ),
    Part(
        3,
        "a_program_end_to_end",
        PART_MACHINE,
        "both",
        "One program from source text to result, with nothing in between left as magic.",
    ),
    Part(
        4,
        "the_operating_system_layer",
        PART_OS,
        "xv6",
        "A kernel small enough to read, taken apart one mechanism at a time.",
    ),
    Part(
        5,
        "where_the_cycles_go",
        PART_COST,
        "host",
        "Part IV's chapters asked again as questions about time.",
    ),
)

#: The five parts that have a page. *Getting started* is the exception and always will be.
PART_PAGES: tuple[Part, ...] = tuple(part for part in PARTS if part.page)


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


def in_part(part: str | Part) -> list[Chapter]:
    title = part.title if isinstance(part, Part) else part
    return [chapter for chapter in CHAPTERS if chapter.part == title]
