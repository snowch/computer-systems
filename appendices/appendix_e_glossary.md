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

## Part I — the machine underneath a program

| Term | Definition | Where |
|---|---|---|
| **translation unit** | One source file plus everything it included, which is what the compiler actually sees. | [ch01](#ch01) |
| **preprocessing** | The first stage: includes pasted in, macros expanded, conditionals resolved. Its output is C. | [ch01](#ch01) |
| **relocation** | A note in an object file saying "this address is not known yet", resolved at link time. | [ch01](#ch01), [ch05](#ch05) |
| **object file** | Compiled code with unresolved references, not yet a program. | [ch01](#ch01) |
| **two's complement** | How signed integers are represented; the reason the negative range is one larger than the positive. | [ch02](#ch02) |
| **integer promotion** | The rule that converts narrow types to `int` before arithmetic, and the source of most signedness surprises. | [ch02](#ch02) |
| **padding** | Bytes a compiler inserts inside a struct so each member lands on an address it can be accessed at. | [ch02](#ch02) |
| **alignment** | The requirement that an object's address be a multiple of its size, or of its widest member. | [ch02](#ch02) |
| **undefined behaviour** | A program the standard makes no promises about, which a compiler may therefore assume never happens. | [ch02](#ch02), [ch03](#ch03) |
| **`volatile`** | A promise not to cache a value in a register and not to reorder accesses to it relative to each other. Not a threading tool. | [ch03](#ch03) |
| **calling convention** | The agreement about which registers carry arguments, which are preserved, and who cleans up. A contract between compiled code, not a hardware rule. | [ch04](#ch04) |
| **caller-saved / callee-saved** | Whether the code making a call or the code being called is responsible for preserving a register across it. | [ch04](#ch04) |
| **stack frame** | The region a function owns on the stack. At `-O2` many functions have none. | [ch04](#ch04) |
| **prologue / epilogue** | The instructions at a function's start and end that establish and dismantle its frame. | [ch04](#ch04) |
| **leaf function** | One that calls nothing, and therefore usually needs no frame and no saved return address. | [ch04](#ch04) |
| **section** | A named region of an object file — what the *linker* deals in. | [ch05](#ch05) |
| **segment** | A named region of a program image — what the *loader* deals in. Sections are mapped into segments. | [ch05](#ch05) |
| **symbol table** | The list of names an object file defines and requires. | [ch05](#ch05) |

## Part II — the kernel, as structure

| Term | Definition | Where |
|---|---|---|
| **trap** | Any transfer to the kernel: a system call, a fault, or an interrupt. The hardware's mechanism is the same for all three. | [ch06](#ch06) |
| **exception** | A trap caused by the instruction being executed — it could not complete. | [ch06](#ch06), [ch09](#ch09) |
| **interrupt** | A trap caused by something outside the program asking for attention. | [ch09](#ch09) |
| **privilege level** | Which of the machine's modes is executing. Changing it is what a trap is for. | [ch06](#ch06) |
| **trampoline** | A page mapped at the same address in every address space, so the trap path survives the page table changing under it. | [ch06](#ch06), [ch07](#ch07) |
| **trap frame** | Where the interrupted program's registers are put, since the interrupted program agreed to no convention. | [ch06](#ch06) |
| **virtual address** | An address a program uses, which means nothing without a page table. | [ch07](#ch07) |
| **page table** | The tree the hardware walks to turn a virtual address into a physical one. | [ch07](#ch07) |
| **Sv39** | RISC-V's three-level paging scheme: three nine-bit indices and a twelve-bit offset. | [ch07](#ch07), [Appendix A](#appendix-a) |
| **page-table entry (PTE)** | One sixty-four-bit word: permission flags and a physical page number, or a pointer to the next level. | [ch07](#ch07) |
| **TLB** | The cache of recent translations. Changing a page table means telling it. | [ch07](#ch07), [ch19](#ch19) |
| **page fault** | A trap raised when translation fails. Not an error — a hook, and most of what a modern kernel does with memory is built on it. | [ch08](#ch08) |
| **lazy allocation** | Handing out address space and only finding physical pages when they are touched. | [ch08](#ch08) |
| **copy-on-write** | Sharing a page until somebody writes to it, using the fault as the trigger. | [ch08](#ch08) |
| **minor fault** | One the kernel satisfies without touching storage. | [ch19](#ch19) |
| **major fault** | One that has to wait for storage. Orders of magnitude more expensive, and identical from the trap's point of view. | [ch19](#ch19) |
| **device driver** | The code that knows a device's registers. In xv6, small enough to read in full. | [ch09](#ch09) |
| **interrupt controller** | The hardware that decides which device may interrupt which core. | [ch09](#ch09) |
| **spinlock** | A lock that waits by running. Correct when the wait is shorter than a context switch. | [ch10](#ch10) |
| **sleeplock** | A lock that waits by yielding. Correct when it is not. | [ch10](#ch10) |
| **memory ordering** | Which of one core's writes another core may observe, and in what order. Weaker than the program order on both of this book's architectures. | [ch10](#ch10), [ch18](#ch18) |
| **barrier / fence** | An instruction, or a property of one, constraining that order. | [ch10](#ch10), [ch18](#ch18) |
| **acquire / release** | The two halves of the ordering a lock needs: nothing moves out of the critical section past either end. | [ch10](#ch10) |
| **context switch** | Saving one thread's registers and restoring another's. Structurally small; what surrounds it is not. | [ch11](#ch11) |
| **scheduler** | The code that decides which thread runs next. | [ch11](#ch11) |
| **buffer cache** | The kernel's copy of recently used disk blocks, and the reason a read can cost nothing. | [ch12](#ch12) |
| **write-ahead log** | Writing what you are about to do before doing it, so a crash leaves a recoverable state. | [ch12](#ch12) |
| **write amplification** | How many blocks actually move for each block a program asked to write. | [ch12](#ch12) |
| **inode** | The on-disk record of a file, distinct from any name it has. | [ch12](#ch12) |

## Part III — where the cycles go

| Term | Definition | Where |
|---|---|---|
| **monotonic clock** | One that cannot go backwards and is not adjusted to keep wall-clock time honest. The only kind to measure with. | [ch14](#ch14) |
| **clock cost** | What reading the clock costs. The number that decides whether a measurement means anything. | [ch14](#ch14), [ch19](#ch19) |
| **distribution** | What to report instead of a number: minimum, median, tail. A single duration is an anecdote. | [ch14](#ch14) |
| **warm-up** | Discarding the start of a run, only when the discarded part is genuinely slower and you can say why. | [ch14](#ch14) |
| **cache line** | The unit everything happens in. Not the variable, not the byte. | [ch15](#ch15), [ch18](#ch18) |
| **working set** | How much memory a piece of code touches in the window that matters. | [ch15](#ch15), [ch20](#ch20) |
| **prefetch** | The hardware fetching ahead of a predictable access pattern, and the reason a sequential walk is not a sequence of misses. | [ch15](#ch15) |
| **pointer chase** | A walk whose next address is not known until the current load returns, which defeats prefetching. | [ch13](#ch13), [ch15](#ch15) |
| **strength reduction** | Replacing an expensive operation with a cheaper one that computes the same thing. Usually the compiler's job. | [ch16](#ch16) |
| **pipeline** | The core overlapping the stages of consecutive instructions. | [ch17](#ch17) |
| **instruction-level parallelism (ILP)** | How many independent instructions are available to overlap. | [ch17](#ch17) |
| **IPC** | Instructions retired per cycle. Above one on a superscalar core, and a diagnostic rather than a goal. | [ch17](#ch17), [ch19](#ch19) |
| **dependence chain** | A sequence where each instruction needs the previous one's result. Its length is a floor no width removes. | [ch17](#ch17), [ch21](#ch21) |
| **branch predictor** | The hardware guessing which way a branch goes, so the pipeline need not wait. | [ch17](#ch17) |
| **misprediction** | A wrong guess, paid for by discarding the work done since. | [ch17](#ch17) |
| **branchless** | Computing both sides and selecting, so there is nothing to mispredict. Worth it exactly when the branch is unpredictable. | [ch17](#ch17) |
| **coherence** | The guarantee that cores agree about the contents of a cache line, and the traffic that provides it. | [ch18](#ch18) |
| **false sharing** | Two cores fighting over a line neither shares data on. The sharing is real; what is false is that anyone meant to share. | [ch18](#ch18) |
| **Amdahl's law** | The ceiling a scaling curve cannot pass, computed from the program before the machine is involved. | [ch18](#ch18) |
| **system call** | A request to the kernel. Compiled into your program as a branch, with the trap somewhere you cannot see. | [ch06](#ch06), [ch19](#ch19) |
| **vDSO** | Kernel code mapped into every process so a few requests need no privilege change at all. The reason the clock is cheap. | [ch19](#ch19) |
| **sampling profiler** | One that arranges to be interrupted and writes down where the program was. Everything it can and cannot tell you follows from that. | [ch20](#ch20) |
| **exclusive / inclusive time** | Samples in a function itself, against samples in it and everything it called. The flat list blames the leaf. | [ch20](#ch20) |
| **skid** | The gap between the instruction that stalled and the one the sample was attributed to. Read the neighbourhood, never the line. | [ch20](#ch20) |
| **aliasing (sampling)** | A fixed sampling period over a fixed loop visiting only some positions, producing a stable and confidently wrong profile. | [ch20](#ch20) |
| **vectorisation** | One instruction doing several elements. Not on by default at the level most people build at. | [ch21](#ch21) |
| **lane** | One element's worth of a vector register. | [ch21](#ch21) |
| **tail** | The elements left over when the trip count is not a multiple of the width, handled one at a time. | [ch21](#ch21) |
| **reassociation** | Adding the same numbers in a different order. Free for integers, not free for floats, and the reason one reduction widens and the other does not. | [ch21](#ch21) |
| **arithmetic bound** | The most a change could possibly buy, computed before measuring. A speedup is reported against it or not reported. | [ch18](#ch18), [ch21](#ch21) |

## What this cannot tell you

**Enough to use any of these.** A one-line definition is for recognising a term you have met. The
chapter named beside it is where it is established, and none of these entries is a substitute for
the measurement that made the chapter worth writing.

**The standard meaning.** Where a term is used here more narrowly than in general practice — and
several are — this page gives the book's sense. Where the book's sense differs from the common one
deliberately, the chapter says so.
