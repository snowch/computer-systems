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
| **target** | One of two places code runs: `xv6` (the teaching kernel under QEMU) or `host` (Linux on real hardware, natively). Every result declares one. [ch00](#ch00) |
| **stamped result** | A JSON file under `bench/results/` carrying what was measured, on which machine, with which toolchain, and a hash of the code that produced it. Nothing reaches a chapter any other way. [ch00](#ch00) |
| **pending figure** | A measurement the book owes but has not taken. It renders as a warning containing no numbers — never a placeholder and never an estimate. [ch00](#ch00) |
| **listing** | Disassembly captured from a compiler and stamped, so a chapter can show machine code without pasting it. Re-captured by CI on every push. [ch00](#ch00) |

## Part II — the machine underneath a program

| Term | Definition | Where |
|---|---|---|
| **translation unit** | One source file plus everything it included, which is what the compiler actually sees. | [ch04](#ch04) |
| **preprocessing** | The first stage: includes pasted in, macros expanded, conditionals resolved. Its output is C. | [ch04](#ch04) |
| **relocation** | A note in an object file saying "this address is not known yet", resolved at link time. | [ch04](#ch04), [ch07](#ch07) |
| **object file** | Compiled code with unresolved references, not yet a program. | [ch04](#ch04) |
| **two's complement** | How signed integers are represented; the reason the negative range is one larger than the positive. | [ch05](#ch05) |
| **integer promotion** | The rule that converts narrow types to `int` before arithmetic, and the source of most signedness surprises. | [ch05](#ch05) |
| **padding** | Bytes a compiler inserts inside a struct so each member lands on an address it can be accessed at. | [ch05](#ch05) |
| **alignment** | The requirement that an object's address be a multiple of its size, or of its widest member. | [ch05](#ch05) |
| **undefined behaviour** | A program the standard makes no promises about, which a compiler may therefore assume never happens. | [ch05](#ch05), [ch03](#ch03) |
| **`volatile`** | A promise not to cache a value in a register and not to reorder accesses to it relative to each other. Not a threading tool. | [ch03](#ch03) |
| **calling convention** | The agreement about which registers carry arguments, which are preserved, and who cleans up. A contract between compiled code, not a hardware rule. | [ch06](#ch06) |
| **caller-saved / callee-saved** | Whether the code making a call or the code being called is responsible for preserving a register across it. | [ch06](#ch06) |
| **stack frame** | The region a function owns on the stack. At `-O2` many functions have none. | [ch06](#ch06) |
| **prologue / epilogue** | The instructions at a function's start and end that establish and dismantle its frame. | [ch06](#ch06) |
| **leaf function** | One that calls nothing, and therefore usually needs no frame and no saved return address. | [ch06](#ch06) |
| **section** | A named region of an object file — what the *linker* deals in. | [ch07](#ch07) |
| **segment** | A named region of a program image — what the *loader* deals in. Sections are mapped into segments. | [ch07](#ch07) |
| **symbol table** | The list of names an object file defines and requires. | [ch07](#ch07) |

## Part III — the kernel, as structure

| Term | Definition | Where |
|---|---|---|
| **trap** | Any transfer to the kernel: a system call, a fault, or an interrupt. The hardware's mechanism is the same for all three. | [ch08](#ch08) |
| **exception** | A trap caused by the instruction being executed — it could not complete. | [ch08](#ch08), [ch11](#ch11) |
| **interrupt** | A trap caused by something outside the program asking for attention. | [ch11](#ch11) |
| **privilege level** | Which of the machine's modes is executing. Changing it is what a trap is for. | [ch08](#ch08) |
| **trampoline** | A page mapped at the same address in every address space, so the trap path survives the page table changing under it. | [ch08](#ch08), [ch09](#ch09) |
| **trap frame** | Where the interrupted program's registers are put, since the interrupted program agreed to no convention. | [ch08](#ch08) |
| **virtual address** | An address a program uses, which means nothing without a page table. | [ch09](#ch09) |
| **page table** | The tree the hardware walks to turn a virtual address into a physical one. | [ch09](#ch09) |
| **Sv39** | RISC-V's three-level paging scheme: three nine-bit indices and a twelve-bit offset. | [ch09](#ch09), [Appendix A](#appendix-a) |
| **page-table entry (PTE)** | One sixty-four-bit word: permission flags and a physical page number, or a pointer to the next level. | [ch09](#ch09) |
| **TLB** | The cache of recent translations. Changing a page table means telling it. | [ch09](#ch09), [ch21](#ch21) |
| **page fault** | A trap raised when translation fails. Not an error — a hook, and most of what a modern kernel does with memory is built on it. | [ch10](#ch10) |
| **lazy allocation** | Handing out address space and only finding physical pages when they are touched. | [ch10](#ch10) |
| **copy-on-write** | Sharing a page until somebody writes to it, using the fault as the trigger. | [ch10](#ch10) |
| **minor fault** | One the kernel satisfies without touching storage. | [ch21](#ch21) |
| **major fault** | One that has to wait for storage. Orders of magnitude more expensive, and identical from the trap's point of view. | [ch21](#ch21) |
| **device driver** | The code that knows a device's registers. In xv6, small enough to read in full. | [ch11](#ch11) |
| **interrupt controller** | The hardware that decides which device may interrupt which core. | [ch11](#ch11) |
| **spinlock** | A lock that waits by running. Correct when the wait is shorter than a context switch. | [ch12](#ch12) |
| **sleeplock** | A lock that waits by yielding. Correct when it is not. | [ch12](#ch12) |
| **memory ordering** | Which of one core's writes another core may observe, and in what order. Weaker than the program order on both of this book's architectures. | [ch12](#ch12), [ch20](#ch20) |
| **barrier / fence** | An instruction, or a property of one, constraining that order. | [ch12](#ch12), [ch20](#ch20) |
| **acquire / release** | The two halves of the ordering a lock needs: nothing moves out of the critical section past either end. | [ch12](#ch12) |
| **context switch** | Saving one thread's registers and restoring another's. Structurally small; what surrounds it is not. | [ch13](#ch13) |
| **scheduler** | The code that decides which thread runs next. | [ch13](#ch13) |
| **buffer cache** | The kernel's copy of recently used disk blocks, and the reason a read can cost nothing. | [ch14](#ch14) |
| **write-ahead log** | Writing what you are about to do before doing it, so a crash leaves a recoverable state. | [ch14](#ch14) |
| **write amplification** | How many blocks actually move for each block a program asked to write. | [ch14](#ch14) |
| **inode** | The on-disk record of a file, distinct from any name it has. | [ch14](#ch14) |

## Part IV — where the cycles go

| Term | Definition | Where |
|---|---|---|
| **monotonic clock** | One that cannot go backwards and is not adjusted to keep wall-clock time honest. The only kind to measure with. | [ch16](#ch16) |
| **clock cost** | What reading the clock costs. The number that decides whether a measurement means anything. | [ch16](#ch16), [ch21](#ch21) |
| **distribution** | What to report instead of a number: minimum, median, tail. A single duration is an anecdote. | [ch16](#ch16) |
| **warm-up** | Discarding the start of a run, only when the discarded part is genuinely slower and you can say why. | [ch16](#ch16) |
| **cache line** | The unit everything happens in. Not the variable, not the byte. | [ch17](#ch17), [ch20](#ch20) |
| **working set** | How much memory a piece of code touches in the window that matters. | [ch17](#ch17), [ch22](#ch22) |
| **prefetch** | The hardware fetching ahead of a predictable access pattern, and the reason a sequential walk is not a sequence of misses. | [ch17](#ch17) |
| **pointer chase** | A walk whose next address is not known until the current load returns, which defeats prefetching. | [ch15](#ch15), [ch17](#ch17) |
| **strength reduction** | Replacing an expensive operation with a cheaper one that computes the same thing. Usually the compiler's job. | [ch18](#ch18) |
| **pipeline** | The core overlapping the stages of consecutive instructions. | [ch19](#ch19) |
| **instruction-level parallelism (ILP)** | How many independent instructions are available to overlap. | [ch19](#ch19) |
| **IPC** | Instructions retired per cycle. Above one on a superscalar core, and a diagnostic rather than a goal. | [ch19](#ch19), [ch21](#ch21) |
| **dependence chain** | A sequence where each instruction needs the previous one's result. Its length is a floor no width removes. | [ch19](#ch19), [ch23](#ch23) |
| **branch predictor** | The hardware guessing which way a branch goes, so the pipeline need not wait. | [ch19](#ch19) |
| **misprediction** | A wrong guess, paid for by discarding the work done since. | [ch19](#ch19) |
| **branchless** | Computing both sides and selecting, so there is nothing to mispredict. Worth it exactly when the branch is unpredictable. | [ch19](#ch19) |
| **coherence** | The guarantee that cores agree about the contents of a cache line, and the traffic that provides it. | [ch20](#ch20) |
| **false sharing** | Two cores fighting over a line neither shares data on. The sharing is real; what is false is that anyone meant to share. | [ch20](#ch20) |
| **Amdahl's law** | The ceiling a scaling curve cannot pass, computed from the program before the machine is involved. | [ch20](#ch20) |
| **system call** | A request to the kernel. Compiled into your program as a branch, with the trap somewhere you cannot see. | [ch08](#ch08), [ch21](#ch21) |
| **vDSO** | Kernel code mapped into every process so a few requests need no privilege change at all. The reason the clock is cheap. | [ch21](#ch21) |
| **sampling profiler** | One that arranges to be interrupted and writes down where the program was. Everything it can and cannot tell you follows from that. | [ch22](#ch22) |
| **exclusive / inclusive time** | Samples in a function itself, against samples in it and everything it called. The flat list blames the leaf. | [ch22](#ch22) |
| **skid** | The gap between the instruction that stalled and the one the sample was attributed to. Read the neighbourhood, never the line. | [ch22](#ch22) |
| **aliasing (sampling)** | A fixed sampling period over a fixed loop visiting only some positions, producing a stable and confidently wrong profile. | [ch22](#ch22) |
| **vectorisation** | One instruction doing several elements. Not on by default at the level most people build at. | [ch23](#ch23) |
| **lane** | One element's worth of a vector register. | [ch23](#ch23) |
| **tail** | The elements left over when the trip count is not a multiple of the width, handled one at a time. | [ch23](#ch23) |
| **reassociation** | Adding the same numbers in a different order. Free for integers, not free for floats, and the reason one reduction widens and the other does not. | [ch23](#ch23) |
| **arithmetic bound** | The most a change could possibly buy, computed before measuring. A speedup is reported against it or not reported. | [ch20](#ch20), [ch23](#ch23) |

## What this cannot tell you

**Enough to use any of these.** A one-line definition is for recognising a term you have met. The
chapter named beside it is where it is established, and none of these entries is a substitute for
the measurement that made the chapter worth writing.

**The standard meaning.** Where a term is used here more narrowly than in general practice — and
several are — this page gives the book's sense. Where the book's sense differs from the common one
deliberately, the chapter says so.
