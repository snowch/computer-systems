---
title: "Systems From Scratch"
short_title: Preface
---

(preface)=
# Systems From Scratch

*From bits to cycles, measured on real hardware.*

A self-study text on computer systems and performance, in five parts and thirty-two chapters.

## What it is about

This book teaches you to find out where a program's time actually goes, and to know when your
answer is wrong. It is easy to learn that a cache miss is expensive, or that a system call costs
more than a function call. It is much harder to measure it yourself — on a machine in front of
you, for a program you did not write — and to know whether the number you got can be trusted.

## What it covers

You work up the layers, from the bits a value is made of to a whole program on real hardware: how
data is represented, how C becomes machine code, how a program is linked and loaded, what the
operating system does to run it, and what the CPU does with it. Each layer gets the same three
questions: how does it work, what does it cost, and how do you measure that cost without fooling
yourself?

## What you will be able to do

Concretely, and these are the things the problems make you do rather than read about:

- Take a duration on a real machine and say whether it means anything — what the clock cost, how
  many repetitions, which statistic, and what the measurement could not see.
- Read the disassembly of a function you wrote and account for what the compiler did with it.
- Stop a kernel in the middle of a trap and say what state is where, and why it had to be saved.
- Find the expensive part of a program you did not write, and know when the profiler is lying to
  you about which line it is.
- Predict a cost from a model before measuring, then say what the gap between the two means.

What you will not get is a table of costs to memorise. Every cost in this book belongs to the one
board that produced it — not to every board of that model, and not to Arm or to computers in
general — and the line under each figure says which machine, which compiler and what day. What
carries to your machine is the method. That is what the list above is.

## Who it is for

Someone who has spent years around computers and programs fluently — a scripting language, or
Java, or anything else with a runtime underneath it — and who has never had a reason to write C or
read a kernel.

**You do not need to know C.** Three of [Part I](#part1)'s four chapters are about exactly that,
and none of them is a C tutorial: control flow, functions and operators are assumed from whatever
language you already use. What it teaches is the part your language was built to hide — that memory is one array of
bytes and everything in it has an index — and then the assumptions that stop holding when there is
no runtime underneath you. [ch02](#reading-a-listing) comes first and is for everyone — it teaches reading what the compiler
produced, which every later chapter asks you to do. Then [ch03](#memory-is-one-array) is the
on-ramp; [ch04](#c-without-a-runtime) is the unlearning;
[ch05](#c-for-people-who-will-read-a-kernel) sorts C's constructs by a single question, *has the machine heard of this?*

**You do not need OS internals.** That is [Part IV](#part4), and it is the point of using a kernel small
enough to read rather than one that has to be described.

**You do not need any hardware background.** No digital logic, and no pipeline diagram.
[Part II](#part2) starts at a bare machine and adds one mechanism at a time, so nothing about the
hardware is assumed before it is built. [ch27](#the-cpu) does the same for the pipeline, on the
grounds that a reader who has seen a five-stage diagram in a lecture still has no idea what a real
core does with a branch.

### Where this is meant to deliver you

This book is an on-ramp. The destination it was written against is *Systems Performance*
@gregg-sysperf — a book that assumes you already know what a system call costs, what a cache miss
is, why a profiler can blame the wrong line, and what a context switch moves. This one establishes
exactly that substrate, by measuring it on a machine you own.

What it deliberately does **not** cover, and what you should read that book for: tracing and BPF,
flame graphs, the network and storage stacks, containers and cloud, and observability across many
machines. There is no overlap to speak of. The relationship is one-way — this is the layer
underneath, and the reason to read it first is that those tools all report quantities whose
meaning is what this book establishes.

## What this book is

Three things make it the shape it is.

**Every number in it was measured, and says where.** No figure is typed into the prose. Each one
comes from a stamped result recording the machine, the kernel, the compiler and a hash of the code
that produced it, and a check fails if a quoted figure stops matching the code in the repository.
Where a measurement has not been taken, you get a box saying so rather than a plausible-looking
placeholder.

**Every problem is a test, and there is no answer key.** Each chapter ends with problems that are
stubs under `tests/`, with a test that passes only when you have solved it. Nothing in the
repository contains the answers — which also means there is no answer key to be wrong.

**Every chapter ends by saying what it could not show you.** A section called *What this cannot
tell you* is mandatory, and it is where the target, the tooling or the hardware ran out. It is
usually the most useful part of the chapter.

:::{note} Where this book is
All thirty-two chapters are written, and eight of the eight appendices.

Zero figures are marked *pending*: the reference machine has reported and every `host` measurement
has been taken, and [Appendix C](#appendix-c) — the perf events this board exposes — is generated
from it rather than drafted from a desk, which is the one thing it could never have been.

**[Download the whole book as a PDF](/systems-from-scratch.pdf)** — every chapter and appendix in
one file, built from the same source as this site, so the two cannot disagree about what a
chapter says.

```{include} _build_stamp.md
```
:::

## How the book is arranged

| | |
|---|---|
| **[Part I](#part1)** — C, and what the machine does with it | Four chapters. The first is for everyone; which of the rest you need depends on where you are starting. Not a C tutorial |
| **[Part II](#part2)** — The machine with nothing on it | A trap, an interrupt, a page table, a system call, file descriptors and `fork()`, each built from nothing on bare hardware before any kernel is read |
| **[Part III](#part3)** — What a computer does with a program | One program from source text to result: the toolchain, representation, machine code, linking |
| **[Part IV](#part4)** — The operating system layer | A kernel small enough to read, taken apart: traps, virtual memory, faults, drivers, locks, scheduling, files |
| **[Part V](#part5)** — Where the cycles go | [Part IV](#part4)'s chapters asked again as questions about time, on hardware that can answer them |

**The sequence is an argument, not a filing order.** [Part II](#part2) takes the machine's
primitives one at a time because a kernel presents them entangled — the first trap you meet in a
real one arrives with a process table, a scheduler and a lock already attached. [Part III](#part3)
is next because a kernel is a program, and you cannot usefully read one until you know what a
program is and who finishes what the compiler left undone; [ch15](#linking-and-loading) ends at
`exec`, which is where [Part IV](#part4) begins. [Part IV](#part4) puts the entanglement back, and
it turns out to be most of what an operating system is.

[Getting started](#part0) sits before all of it: [ch00](#prerequisites-and-setup) is the emulated
targets and a script that says what your machine can currently run, and
[ch01](#setting-up-the-board) is the board, whenever it arrives.

[Part IV](#part4) reads a real kernel, and that kernel has a book of its own: *xv6: a simple,
Unix-like teaching operating system* @xv6-book, written by its authors and free from MIT. The two
do different jobs — it explains what the code does, this book asks what that costs — and they go
well together. [Appendix G](#appendix-g) lines them up by topic rather than by chapter number,
because its numbering moves between revisions. The same appendix traces one system call through
every layer it touches.

## Three targets on two machines, on purpose

Almost every book on this subject picks one target and lives with its limitations. This one uses
three, because the question has halves that need different instruments.

```{figure} chapters/_figures/prerequisites-and-setup-targets.svg
:alt: The bare, xv6 and host targets side by side, with what each can and cannot answer.
:width: 100%

The division of labour. Every chapter declares which target it uses, and every figure records
which one produced it.
```

The three are `bare` (a RISC-V machine under QEMU with no kernel on it at all), `xv6` (the MIT
teaching kernel under the same QEMU), and `host` (a real Linux machine, a Raspberry Pi 5 by
default); [ch00](#prerequisites-and-setup) sets them up and says what each can and cannot answer.
That is three targets on **two machines**: the first two are both QEMU on the computer you are
reading this on, and need one cross-compiler between them. Only the third has to be real.
[Part III](#part3) works on both sides of the split, and
[ch12](#what-a-computer-does-with-a-program) is where it crosses.

The split is not a compromise; it is the argument. QEMU will happily answer a question about
nanoseconds and the answer will be meaningless, because it models no cache, no branch predictor
and no pipeline. Watching a program in a debugger tells you what it *does*. Only real hardware
tells you what it *costs*. [ch23](#the-same-program-on-both-targets) puts the same program through both and makes
the gap concrete.

### Why they do not share an instruction set

The kernel small enough to read in an afternoon is a RISC-V kernel. The hardware whose counters
actually work is an ARM one. Those are different machines, and pretending otherwise would mean
lying about one of them.

[Part V](#part5) needs `perf` to do two separate things: **count** events over a run, and **sample** —
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

Read down the columns. Choosing RISC-V for [Part V](#part5) would have made two of its eight chapters
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

**You get two memory models instead of one.** [ch20](#locks-and-memory-ordering) teaches RISC-V's;
[ch28](#memory-ordering-on-real-hardware) measures ARM's, which is also weak and differently specified. A reader shown only one would reasonably
conclude that model *is* memory ordering. Shown two, you learn it is a family, that a fence is an
architecture-specific spelling of an architecture-independent need, and that store buffers and
coherence are what actually transfer.

**[ch23](#the-same-program-on-both-targets) gets harder in the way that matters.** Three things differ between watching a program
under xv6 and profiling it on real hardware: emulation against hardware, one kernel against
another, one instruction set against another. Attributing a difference to the wrong one is the
commonest way to be confidently wrong about performance, and that chapter is where you practise
separating them.

Reading disassembly is a small part of the book, and this is the whole of what the split costs
you. After that, in Parts I and III it is RISC-V: [ch03](#memory-is-one-array),
[ch05](#c-for-people-who-will-read-a-kernel), [ch12](#what-a-computer-does-with-a-program),
[ch13](#representing-information) and [ch14](#machine-level-code-on-riscv). In
[Part V](#part5) it is AArch64: [ch26](#optimising-code), [ch27](#the-cpu),
[ch29](#the-os-layers-cost), [ch30](#whole-machine-profiling) and [ch31](#vectors). Two chapters print both at once because
the comparison is the content — [ch20](#locks-and-memory-ordering) on what an atomic looks like
either way, and [ch23](#the-same-program-on-both-targets) on one program compiled for each.
[ch02](#reading-a-listing) is the third, and comes first: it shows one small function both ways so
the difference is concrete rather than promised. [Appendix F](#appendix-f) is a translation
between the two for the reader who meets the second having learned the first. Everything else is
method, and method does not have an architecture.

### One argument, not two tutorials

**[Part V](#part5) is not a second book. It is [Part IV](#part4)'s chapters asked again as questions about time.**
Every chapter in it names the earlier chapter whose cost it measures, in its own header:

| When [Part V](#part5) asks | You already learned the mechanism in |
|---|---|
| [ch25](#the-memory-hierarchy) — where is the data, and what does each step outward cost? | [ch13](#representing-information) layout and alignment, [ch17](#virtual-memory) address translation |
| [ch26](#optimising-code) — what did that cost? | [ch14](#machine-level-code-on-riscv) what the compiler emitted |
| [ch27](#the-cpu) — what is the core doing between fetch and finish? | [ch14](#machine-level-code-on-riscv) the instructions themselves |
| [ch28](#memory-ordering-on-real-hardware) — what do four cores cost each other? | [ch20](#locks-and-memory-ordering) locks, fences and ordering |
| [ch29](#the-os-layers-cost) — what does Linux charge for this? | [ch16](#traps-and-system-calls) traps, [ch18](#page-faults-as-a-feature) faults, [ch21](#scheduling-and-context-switches) switches |

So you never arrive at a [Part V](#part5) chapter cold. You arrive knowing the mechanism completely and
needing only the price — a better position than either half could put you in alone, and the reason
the book is arranged this way rather than as theory followed by benchmarks.

Three [Part V](#part5) chapters have no counterpart, deliberately: [ch24](#measuring) teaches measurement
itself, [ch30](#whole-machine-profiling) is about the whole machine rather than any one mechanism, and
[ch31](#vectors) concerns hardware [Part IV](#part4) never had reason to describe.

## How the numbers work

The stamped result behind each figure is a JSON file under `bench/results/`, and it records the
target, the board or QEMU version, the kernel, the compiler, its flags, and a hash of the code
that produced the number.

The consequence worth stating plainly is what happens when a machine cannot answer a question at
all. The chapter says so, shows the reasoning it used instead, and does not quietly substitute a
number from somewhere else. The chapters whose reading depends on something specific about the
reference machine say so in their own headers rather than letting you discover it two hundred
pages in.

## What you will need

A laptop for [ch00](#prerequisites-and-setup) and for Parts I to IV — everything there runs under
emulation, free. A small Linux machine whose `perf` can count and sample for
[ch01](#setting-up-the-board) and [Part V](#part5); a Raspberry Pi 5 is the reference, and one you
already own may well do — [Appendix H](#appendix-h) is how to tell. Twenty-two chapters sit
between needing the first and needing the second.

The book does not tell you which kernel to run. Whether a machine's performance counters work is
a property of its whole configuration — silicon, device tree, kernel, firmware — rather than of
the board, and the reference board's own counters went missing for a kernel release. So every
figure records the image and kernel that produced it, and
[ch00](#prerequisites-and-setup) hands you a script that asks your machine instead of a version
number to match.

## Problems

Every chapter ends with problems, and every problem is a stub under `tests/` with a test that
passes only when you have solved it. There is no answer key at the back — which means there is no
answer key to be wrong.
