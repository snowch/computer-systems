---
title: "Appendix E — Glossary"
short_title: "Appendix E"
---

(appendix-e)=
# Appendix E · Glossary

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

Assembled from the chapters after they were written, which is the only order that works: a
glossary drafted first defines the words the prose did not end up using. Every entry names the
chapter that establishes it, and the definition here is deliberately shorter than the chapter's —
this page is for recognising a term, not for learning it.

## The book's own vocabulary

These four are used throughout and mean something specific here.

| Term | What it means in this book |
|---|---|
| **target** | One of two places code runs: `xv6` (the teaching kernel under QEMU) or `host` (Linux on real hardware, natively). Every result declares one. [ch00](#prerequisites-and-setup) |
| **stamped result** | A JSON file under `bench/results/` carrying what was measured, on which machine, with which toolchain, and a hash of the code that produced it. Nothing reaches a chapter any other way. [ch00](#prerequisites-and-setup) |
| **pending figure** | A measurement the book owes but has not taken. It renders as a warning containing no numbers — never a placeholder and never an estimate. [ch00](#prerequisites-and-setup) |
| **listing** | Disassembly captured from a compiler and stamped, so a chapter can show machine code without pasting it. Re-captured by CI on every push. [ch00](#prerequisites-and-setup) |

## Part III — the machine underneath a program

| Term | Definition | Where |
|---|---|---|
| **translation unit** | One source file plus everything it included, which is what the compiler actually sees. | [ch10](#what-a-computer-does-with-a-program) |
| **preprocessing** | The first stage: includes pasted in, macros expanded, conditionals resolved. Its output is C. | [ch10](#what-a-computer-does-with-a-program) |
| **relocation** | A note in an object file saying "this address is not known yet", resolved at link time. | [ch10](#what-a-computer-does-with-a-program), [ch13](#linking-and-loading) |
| **object file** | Compiled code with unresolved references, not yet a program. | [ch10](#what-a-computer-does-with-a-program) |
| **two's complement** | How signed integers are represented; the reason the negative range is one larger than the positive. | [ch11](#representing-information) |
| **integer promotion** | The rule that converts narrow types to `int` before arithmetic, and the source of most signedness surprises. | [ch11](#representing-information) |
| **padding** | Bytes a compiler inserts inside a struct so each member lands on an address it can be accessed at. | [ch11](#representing-information) |
| **alignment** | The requirement that an object's address be a multiple of its size, or of its widest member. | [ch11](#representing-information) |
| **undefined behaviour** | A program the standard makes no promises about, which a compiler may therefore assume never happens. | [ch11](#representing-information), [ch03](#c-for-people-who-will-read-a-kernel) |
| **`volatile`** | A promise not to cache a value in a register and not to reorder accesses to it relative to each other. Not a threading tool. | [ch03](#c-for-people-who-will-read-a-kernel) |
| **calling convention** | The agreement about which registers carry arguments, which are preserved, and who cleans up. A contract between compiled code, not a hardware rule. | [ch12](#machine-level-code-on-riscv) |
| **caller-saved / callee-saved** | Whether the code making a call or the code being called is responsible for preserving a register across it. | [ch12](#machine-level-code-on-riscv) |
| **stack frame** | The region a function owns on the stack. At `-O2` many functions have none. | [ch12](#machine-level-code-on-riscv) |
| **prologue / epilogue** | The instructions at a function's start and end that establish and dismantle its frame. | [ch12](#machine-level-code-on-riscv) |
| **leaf function** | One that calls nothing, and therefore usually needs no frame and no saved return address. | [ch12](#machine-level-code-on-riscv) |
| **section** | A named region of an object file — what the *linker* deals in. | [ch13](#linking-and-loading) |
| **segment** | A named region of a program image — what the *loader* deals in. Sections are mapped into segments. | [ch13](#linking-and-loading) |
| **symbol table** | The list of names an object file defines and requires. | [ch13](#linking-and-loading) |

## Part IV — the kernel, as structure

| Term | Definition | Where |
|---|---|---|
| **trap** | Any transfer to the kernel: a system call, a fault, or an interrupt. The hardware's mechanism is the same for all three. | [ch14](#traps-and-system-calls) |
| **exception** | A trap caused by the instruction being executed — it could not complete. | [ch14](#traps-and-system-calls), [ch17](#interrupts-and-drivers) |
| **interrupt** | A trap caused by something outside the program asking for attention. | [ch17](#interrupts-and-drivers) |
| **privilege level** | Which of the machine's modes is executing. Changing it is what a trap is for. | [ch14](#traps-and-system-calls) |
| **trampoline** | A page mapped at the same address in every address space, so the trap path survives the page table changing under it. | [ch14](#traps-and-system-calls), [ch15](#virtual-memory) |
| **trap frame** | Where the interrupted program's registers are put, since the interrupted program agreed to no convention. | [ch14](#traps-and-system-calls) |
| **virtual address** | An address a program uses, which means nothing without a page table. | [ch15](#virtual-memory) |
| **page table** | The tree the hardware walks to turn a virtual address into a physical one. | [ch15](#virtual-memory) |
| **Sv39** | RISC-V's three-level paging scheme: three nine-bit indices and a twelve-bit offset. | [ch15](#virtual-memory), [Appendix A](#appendix-a) |
| **page-table entry (PTE)** | One sixty-four-bit word: permission flags and a physical page number, or a pointer to the next level. | [ch15](#virtual-memory) |
| **TLB** | The cache of recent translations. Changing a page table means telling it. | [ch15](#virtual-memory), [ch27](#the-os-layers-cost) |
| **page fault** | A trap raised when translation fails. Not an error — a hook, and most of what a modern kernel does with memory is built on it. | [ch16](#page-faults-as-a-feature) |
| **lazy allocation** | Handing out address space and only finding physical pages when they are touched. | [ch16](#page-faults-as-a-feature) |
| **copy-on-write** | Sharing a page until somebody writes to it, using the fault as the trigger. | [ch16](#page-faults-as-a-feature) |
| **minor fault** | One the kernel satisfies without touching storage. | [ch27](#the-os-layers-cost) |
| **major fault** | One that has to wait for storage. Orders of magnitude more expensive, and identical from the trap's point of view. | [ch27](#the-os-layers-cost) |
| **device driver** | The code that knows a device's registers. In xv6, small enough to read in full. | [ch17](#interrupts-and-drivers) |
| **interrupt controller** | The hardware that decides which device may interrupt which core. | [ch17](#interrupts-and-drivers) |
| **spinlock** | A lock that waits by running. Correct when the wait is shorter than a context switch. | [ch18](#locks-and-memory-ordering) |
| **sleeplock** | A lock that waits by yielding. Correct when it is not. | [ch18](#locks-and-memory-ordering) |
| **memory ordering** | Which of one core's writes another core may observe, and in what order. Weaker than the program order on both of this book's architectures. | [ch18](#locks-and-memory-ordering), [ch26](#memory-ordering-on-real-hardware) |
| **barrier / fence** | An instruction, or a property of one, constraining that order. | [ch18](#locks-and-memory-ordering), [ch26](#memory-ordering-on-real-hardware) |
| **acquire / release** | The two halves of the ordering a lock needs: nothing moves out of the critical section past either end. | [ch18](#locks-and-memory-ordering) |
| **context switch** | Saving one thread's registers and restoring another's. Structurally small; what surrounds it is not. | [ch19](#scheduling-and-context-switches) |
| **scheduler** | The code that decides which thread runs next. | [ch19](#scheduling-and-context-switches) |
| **buffer cache** | The kernel's copy of recently used disk blocks, and the reason a read can cost nothing. | [ch20](#the-file-system) |
| **write-ahead log** | Writing what you are about to do before doing it, so a crash leaves a recoverable state. | [ch20](#the-file-system) |
| **write amplification** | How many blocks actually move for each block a program asked to write. | [ch20](#the-file-system) |
| **inode** | The on-disk record of a file, distinct from any name it has. | [ch20](#the-file-system) |

## Part V — where the cycles go

| Term | Definition | Where |
|---|---|---|
| **monotonic clock** | One that cannot go backwards and is not adjusted to keep wall-clock time honest. The only kind to measure with. | [ch22](#measuring) |
| **clock cost** | What reading the clock costs. The number that decides whether a measurement means anything. | [ch22](#measuring), [ch27](#the-os-layers-cost) |
| **distribution** | What to report instead of a number: minimum, median, tail. A single duration is an anecdote. | [ch22](#measuring) |
| **warm-up** | Discarding the start of a run, only when the discarded part is genuinely slower and you can say why. | [ch22](#measuring) |
| **cache line** | The unit everything happens in. Not the variable, not the byte. | [ch23](#the-memory-hierarchy), [ch26](#memory-ordering-on-real-hardware) |
| **working set** | How much memory a piece of code touches in the window that matters. | [ch23](#the-memory-hierarchy), [ch28](#whole-machine-profiling) |
| **prefetch** | The hardware fetching ahead of a predictable access pattern, and the reason a sequential walk is not a sequence of misses. | [ch23](#the-memory-hierarchy) |
| **pointer chase** | A walk whose next address is not known until the current load returns, which defeats prefetching. | [ch21](#the-same-program-on-both-targets), [ch23](#the-memory-hierarchy) |
| **strength reduction** | Replacing an expensive operation with a cheaper one that computes the same thing. Usually the compiler's job. | [ch24](#optimising-code) |
| **pipeline** | The core overlapping the stages of consecutive instructions. | [ch25](#the-cpu) |
| **instruction-level parallelism (ILP)** | How many independent instructions are available to overlap. | [ch25](#the-cpu) |
| **IPC** | Instructions retired per cycle. Above one on a superscalar core, and a diagnostic rather than a goal. | [ch25](#the-cpu), [ch27](#the-os-layers-cost) |
| **dependence chain** | A sequence where each instruction needs the previous one's result. Its length is a floor no width removes. | [ch25](#the-cpu), [ch29](#vectors) |
| **branch predictor** | The hardware guessing which way a branch goes, so the pipeline need not wait. | [ch25](#the-cpu) |
| **misprediction** | A wrong guess, paid for by discarding the work done since. | [ch25](#the-cpu) |
| **branchless** | Computing both sides and selecting, so there is nothing to mispredict. Worth it exactly when the branch is unpredictable. | [ch25](#the-cpu) |
| **coherence** | The guarantee that cores agree about the contents of a cache line, and the traffic that provides it. | [ch26](#memory-ordering-on-real-hardware) |
| **false sharing** | Two cores fighting over a line neither shares data on. The sharing is real; what is false is that anyone meant to share. | [ch26](#memory-ordering-on-real-hardware) |
| **Amdahl's law** | The ceiling a scaling curve cannot pass, computed from the program before the machine is involved. | [ch26](#memory-ordering-on-real-hardware) |
| **system call** | A request to the kernel. Compiled into your program as a branch, with the trap somewhere you cannot see. | [ch14](#traps-and-system-calls), [ch27](#the-os-layers-cost) |
| **vDSO** | Kernel code mapped into every process so a few requests need no privilege change at all. The reason the clock is cheap. | [ch27](#the-os-layers-cost) |
| **sampling profiler** | One that arranges to be interrupted and writes down where the program was. Everything it can and cannot tell you follows from that. | [ch28](#whole-machine-profiling) |
| **exclusive / inclusive time** | Samples in a function itself, against samples in it and everything it called. The flat list blames the leaf. | [ch28](#whole-machine-profiling) |
| **skid** | The gap between the instruction that stalled and the one the sample was attributed to. Read the neighbourhood, never the line. | [ch28](#whole-machine-profiling) |
| **aliasing (sampling)** | A fixed sampling period over a fixed loop visiting only some positions, producing a stable and confidently wrong profile. | [ch28](#whole-machine-profiling) |
| **vectorisation** | One instruction doing several elements. Not on by default at the level most people build at. | [ch29](#vectors) |
| **lane** | One element's worth of a vector register. | [ch29](#vectors) |
| **tail** | The elements left over when the trip count is not a multiple of the width, handled one at a time. | [ch29](#vectors) |
| **reassociation** | Adding the same numbers in a different order. Free for integers, not free for floats, and the reason one reduction widens and the other does not. | [ch29](#vectors) |
| **arithmetic bound** | The most a change could possibly buy, computed before measuring. A speedup is reported against it or not reported. | [ch26](#memory-ordering-on-real-hardware), [ch29](#vectors) |

## What this cannot tell you

**Enough to use any of these.** A one-line definition is for recognising a term you have met. The
chapter named beside it is where it is established, and none of these entries is a substitute for
the measurement that made the chapter worth writing.

**The standard meaning.** Where a term is used here more narrowly than in general practice — and
several are — this page gives the book's sense. Where the book's sense differs from the common one
deliberately, the chapter says so.
