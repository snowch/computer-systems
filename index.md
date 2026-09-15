---
title: "Systems From Scratch"
short_title: Preface
---

# Systems From Scratch

*From bits to cycles, measured on real hardware.*

:::{warning} This book is being written
[Chapter 0](#ch00) is complete and the toolchain around it works end to end. Every other
chapter is a stub, and every stub names its target, its question and the measurements it owes you
— so the table of contents is already a usable map of where the book is going. The six appendices
each say what they will hold and where that content has to come from. The
[project plan](https://github.com/snowch/computer-systems/blob/main/PLAN.md) has the long version,
and what each chapter must produce before it loses its `[DRAFT]` marker.

**[Download the whole book as a PDF](systems-from-scratch.pdf)** — every chapter and appendix in
one file, built from the same source as this site, so the two cannot disagree about what a
chapter says.
:::

## The question this book keeps asking

**Where do the cycles go, and how would I know?**

That second clause is the whole book. It is easy to learn that a cache miss is expensive, that a
system call costs more than a function call, that branch prediction exists. It is much harder to
be able to *find out* — on a machine in front of you, for a program you did not write — where the
time actually went, and to know when the answer you got is wrong.

So every layer here gets the same treatment: how it works, then what it costs, then how that cost
was measured and what the measurement could not see.

## Two machines, on purpose

Almost every book on this subject picks one target and lives with its limitations. This one uses
two, because the two halves of the question need different things.

```{figure} chapters/_figures/ch00-targets.svg
:alt: The xv6 and host targets side by side, with what each can and cannot answer.
:width: 100%

The division of labour. Every chapter declares which target it uses, and every figure records
which one produced it.
```

The first is **xv6**, the MIT teaching kernel, running under QEMU. It is a complete operating
system small enough to read in an afternoon, and you can stop the whole machine mid-trap and look
at anything. Parts II and III live there.

The second is a small Linux machine on a desk, reached over SSH — a **Raspberry Pi 5** by
default. Every number in Part IV is measured on it, natively. Not in an emulator, not on the
laptop, not extrapolated from a different machine.

The split is not a compromise; it is the argument. QEMU will happily answer a question about
nanoseconds and the answer will be meaningless, because it models no cache, no branch predictor
and no pipeline. Watching a program in a debugger tells you what it *does*. Only real hardware
tells you what it *costs*. [Chapter 13](#ch15) puts the same program through both and makes
the gap concrete.

### Why they do not share an instruction set

The kernel small enough to read in an afternoon is a RISC-V kernel. The hardware whose counters
actually work is an ARM one. Those are different machines, and pretending otherwise would mean
lying about one of them.

Part IV needs `perf` to do two separate things: **count** events over a run, and **sample** —
interrupt the program thousands of times a second to ask where it is. Sampling needs the counters
to raise an interrupt when they overflow. On ARM that is a standard part of the performance
monitoring unit. On RISC-V it is an optional extension, and a 2025 study of the three RISC-V cores
you can actually buy @riscv-pmu-profiling found that none of them wins:

| | SiFive U74 | T-Head C910 | SpacemiT X60 |
|---|---|---|---|
| Out-of-order | No | Yes | No |
| Vector extension | **None** | 0.7.1 (draft) | RVV 1.0 |
| **Counter-overflow interrupt** | **No** | Yes | Limited |
| Upstream Linux support | Yes | Partial | **No** |

Read down the columns. Choosing RISC-V for Part IV would have made two of its eight chapters
unmeasurable — one needs sampling, one needs a vector unit — on boards that are hard to buy, with
firmware that has broken `perf` between distribution releases. A Raspberry Pi costs none of that.

### What the split buys

It would be easy to present that as a regrettable compromise. It is not, and the honest version is
more interesting.

This book's argument is *use the instrument that can answer your question, and know what each
instrument cannot tell you*. Chapter after chapter applies that to caches, to profilers, to
emulators. Applying it to the book's own construction gives exactly this arrangement. Three things
follow that a single-architecture book could not offer.

**The concepts are visibly not about an instruction set.** A book that stays on one architecture
has to *assert* that its ideas generalise. This one demonstrates it, by having them survive a
change of architecture in front of you.

**You get two memory models instead of one.** [Chapter 10](#ch12) teaches RISC-V's;
[chapter 18](#ch20) measures ARM's, which is also weak and differently specified. A reader shown only one would reasonably
conclude that model *is* memory ordering. Shown two, you learn it is a family, that a fence is an
architecture-specific spelling of an architecture-independent need, and that store buffers and
coherence are what actually transfer.

**[Chapter 13](#ch15) gets harder in the way that matters.** Three things differ between watching a program
under xv6 and profiling it on real hardware: emulation against hardware, one kernel against
another, one instruction set against another. Attributing a difference to the wrong one is the
commonest way to be confidently wrong about performance, and that chapter is where you practise
separating them.

Reading disassembly is a small part of the book, and this is the whole of what the split costs
you. In Parts II and III it is RISC-V: [ch04](#ch04) through [ch06](#ch06). In Part IV it is AArch64:
[ch18](#ch18), [ch19](#ch19) and [ch23](#ch23). Chapter 0 shows one small function compiled both ways, so the difference is concrete rather
than promised, and [Appendix F](#appendix-f) is a translation between the two for the reader who
meets the second having learned the first. Everything else is method, and method does not have an
architecture.

### One argument, not two tutorials

**Part IV is not a second book. It is Part III's chapters asked again as questions about time.**
Every chapter in it names the earlier chapter whose cost it measures, in its own header:

| When Part IV asks | You already learned the mechanism in |
|---|---|
| [ch17](#ch17) — where is the data, and what does each step out cost? | [ch05](#ch05) layout and alignment, [ch09](#ch09) address translation |
| [ch18](#ch18) — what did that cost? | [ch06](#ch06) what the compiler emitted |
| [ch19](#ch19) — what is the core doing between fetch and finish? | [ch06](#ch06) the instructions themselves |
| [ch20](#ch20) — what do four cores cost each other? | [ch12](#ch12) locks, fences and ordering |
| [ch21](#ch21) — what does Linux charge for this? | [ch08](#ch08) traps, [ch10](#ch10) faults, [ch13](#ch13) switches |

So you never arrive at a Part IV chapter cold. You arrive knowing the mechanism completely and
needing only the price — a better position than either half could put you in alone, and the reason
the book is arranged this way rather than as theory followed by benchmarks.

Three Part IV chapters have no counterpart, deliberately: [ch16](#ch16) teaches measurement
itself, [ch22](#ch22) is about the whole machine rather than any one mechanism, and
[ch23](#ch23) concerns hardware Part III never had reason to describe.

## How the numbers work

Every figure in this book comes from a JSON file under `bench/results/` that records the target,
the board or QEMU version, the kernel, the compiler, its flags, and a hash of the code that
produced the number. Nothing is typed into the prose by hand, and CI fails if a quoted figure's
hash stops matching the code in the repository.

Two consequences worth stating plainly. Where a measurement has not been taken yet, you will see
a box saying so rather than a plausible-looking placeholder. And where a machine cannot answer a
question at all, the chapter says that, shows the reasoning it used instead, and does not quietly
substitute a number from somewhere else. Five chapters depend on something specific about the
reference machine, and each says so in its own header rather than letting you discover it two
hundred pages in.

## Who it is for

Someone who has seen digital logic and a pipeline diagram, has spent years around computers, is
fluent in a scripting language, and has never had a reason to read a kernel. You do not need to
know C well; [chapter 3](#ch03) covers the parts that are really about addresses. You do not
need OS internals; that is Part III.

## What you will need

A laptop for Parts II and III — everything there runs under emulation, free. For Part IV, a small
Linux machine whose `perf` can count and sample; a Raspberry Pi 5 is the reference, and one you
already own may well do. [Chapter 0](#ch00) is the setup, and a script that tells you which
targets your machine can currently run and whether its counters are real.

The book does not tell you which kernel to run. Whether a machine's performance counters work is
a property of its whole configuration — silicon, device tree, kernel, firmware — rather than of
the board, and the reference board's own counters went missing for a kernel release. So every
figure records the image and kernel that produced it, and chapter 0 hands you a script that asks
your machine instead of a version number to match.

## Problems

Every chapter ends with problems, and every problem is a stub under `tests/` with a test that
passes only when you have solved it. There is no answer key at the back — which means there is no
answer key to be wrong.
