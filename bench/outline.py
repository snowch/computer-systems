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
    ),
    Chapter(
        1,
        "what_a_computer_does_with_a_program",
        "What a Computer Does With a Program",
        PART_I,
        "both",
        "What actually happens between a source file and a result, and which of it costs anything?",
        "ch01-whole-stack",
    ),
    Chapter(
        2,
        "representing_information",
        "Representing Information",
        PART_I,
        "xv6",
        "What is a number to this machine, and when does that answer bite?",
        "ch02-bits",
    ),
    Chapter(
        3,
        "c_for_people_who_will_read_a_kernel",
        "C for People Who Will Read a Kernel",
        PART_I,
        "xv6",
        "Which parts of C are really about addresses, and how do I read them without flinching?",
        "ch03-c",
    ),
    Chapter(
        4,
        "machine_level_code_on_riscv",
        "Machine-Level Code on RISC-V",
        PART_I,
        "xv6",
        "What did the compiler actually emit, and how do I read it?",
        "ch04-asm",
    ),
    Chapter(
        5,
        "linking_and_loading",
        "Linking and Loading",
        PART_I,
        "xv6",
        "How does a file on disk become an address space?",
        "ch05-elf",
    ),
    Chapter(
        6,
        "traps_and_system_calls",
        "Traps and System Calls",
        PART_II,
        "xv6",
        "What does the hardware do when a program asks the kernel for something?",
        "ch06-traps",
    ),
    Chapter(
        7,
        "virtual_memory",
        "Virtual Memory",
        PART_II,
        "xv6",
        "What is an address, and who decides what it means?",
        "ch07-vm",
    ),
    Chapter(
        8,
        "page_faults_as_a_feature",
        "Page Faults as a Feature",
        PART_II,
        "xv6",
        "What can a kernel do with a fault it expected?",
        "ch08-faults",
    ),
    Chapter(
        9,
        "interrupts_and_drivers",
        "Interrupts and Drivers",
        PART_II,
        "xv6",
        "How does a device get the CPU's attention, and what does the CPU do about it?",
        "ch09-devices",
    ),
    Chapter(
        10,
        "locks_and_memory_ordering",
        "Locks and Memory Ordering",
        PART_II,
        "xv6",
        "What breaks when two harts touch the same memory, and what is the minimum fix?",
        "ch10-locks",
    ),
    Chapter(
        11,
        "scheduling_and_context_switches",
        "Scheduling and Context Switches",
        PART_II,
        "xv6",
        "What exactly is saved, and what does it mean to say a thread 'runs'?",
        "ch11-sched",
    ),
    Chapter(
        12,
        "the_file_system",
        "The File System",
        PART_II,
        "xv6",
        "What has to be true on the disk for a crash mid-write to be survivable?",
        "ch12-fs",
    ),
    Chapter(
        13,
        "the_same_program_on_both_targets",
        "The Same Program on Both Targets",
        PART_II,
        "both",
        "What does watching a program in a debugger fail to tell me about what it costs?",
        "ch13-bridge",
    ),
    Chapter(
        14,
        "measuring",
        "Measuring",
        PART_III,
        "host",
        "How do I get a number I would defend, and how would I know it was wrong?",
        "ch14-measuring",
    ),
    Chapter(
        15,
        "the_memory_hierarchy",
        "The Memory Hierarchy",
        PART_III,
        "host",
        "Where is the data, and what does each extra step out cost?",
        "ch15-memory",
        assumes="a particular cache hierarchy — the levels, sizes, line size and TLB reach "
        "are this core's. The method transfers to any machine; the numbers do not, and "
        "measuring your own is the exercise.",
    ),
    Chapter(
        16,
        "optimising_code",
        "Optimising Code",
        PART_III,
        "host",
        "What will the compiler do for me, and what will it never do?",
        "ch16-optimising",
    ),
    Chapter(
        17,
        "the_cpu",
        "The CPU",
        PART_III,
        "host",
        "What is this core doing between fetching an instruction and finishing it?",
        "ch17-cpu",
        assumes="a specific microarchitecture. The reference is an out-of-order, 4-wide "
        "Cortex-A76; core width, branch predictor and PMU event names all differ elsewhere, "
        "and on an in-order core these experiments get easier to read, not harder.",
    ),
    Chapter(
        18,
        "memory_ordering_on_real_hardware",
        "Memory Ordering on Real Hardware",
        PART_III,
        "host",
        "What do four cores cost each other, and what does a fence actually buy?",
        "ch18-concurrency",
        assumes="four cores, and this interconnect's coherence behaviour. A different core "
        "count moves the scaling curve without changing the mechanism; two cores make the "
        "chapter thin.",
    ),
    Chapter(
        19,
        "the_os_layers_cost",
        "The OS Layer's Cost on Real Hardware",
        PART_III,
        "host",
        "What does Linux charge for the services xv6 showed me?",
        "ch19-os-cost",
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
    ),
    Chapter(
        21,
        "vectors",
        "Vectors",
        PART_III,
        "host",
        "What does vectorising actually buy, and when will the compiler do it for me?",
        None,
        assumes="a vector unit — NEON on the reference core. This chapter became measurable "
        "when Part III moved to AArch64; on a RISC-V board without RVV 1.0 it reverts to "
        "reasoning about code the compiler emits but the hardware cannot run.",
    ),
)


@dataclass(frozen=True)
class Appendix:
    letter: str
    slug: str
    title: str

    @property
    def label(self) -> str:
        return f"appendix-{self.letter.lower()}"

    @property
    def path(self) -> str:
        return f"appendices/appendix_{self.letter.lower()}_{self.slug}.md"


APPENDICES: tuple[Appendix, ...] = (
    Appendix("A", "riscv_reference", "RISC-V Registers and CSRs"),
    Appendix("B", "gdb_reference", "gdb for Kernels and RISC-V"),
    Appendix("C", "perf_events", "The perf Events This Board Has"),
    Appendix("D", "xv6_file_map", "An xv6 File Map"),
    Appendix("E", "glossary", "Glossary"),
)

PARTS: tuple[str, ...] = (PART_I, PART_II, PART_III)


def by_number(number: int) -> Chapter:
    for chapter in CHAPTERS:
        if chapter.number == number:
            return chapter
    raise KeyError(f"no chapter {number}")


def in_part(part: str) -> list[Chapter]:
    return [chapter for chapter in CHAPTERS if chapter.part == part]
