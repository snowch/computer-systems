---
title: "Systems From Scratch"
short_title: Preface
---

# Systems From Scratch

*From bits to cycles, measured on real hardware.*


## What this book is

A self-study text on computer systems and performance, in four parts and twenty-four chapters,
built around one question and a rule about answering it.

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
Twenty-four of the twenty-nine chapters are written, and six of the seven appendices. The five
still being drafted are all of [Part II](#ch04), which teaches each primitive of the machine on
its own before Part IV meets them entangled inside a kernel; each carries its target, its question
and the measurements it owes you, so the table of contents is already a map of where it is going.

Thirteen figures are marked *pending*: they are `host` measurements that have to be taken on the
reference machine, and until they are you will see a box saying so rather than a number. Appendix C
waits for the same machine — which events a board exposes is a property of its silicon, kernel and
firmware together, and cannot be drafted from a desk.

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

## Who it is for

Someone who has spent years around computers and programs fluently — a scripting language, or
Java, or anything else with a runtime underneath it — and who has never had a reason to write C or
read a kernel.

**You do not need to know C.** Part I is three chapters about exactly that, and it is not a C
tutorial: control flow, functions and operators are assumed from whatever language you already
use. What it teaches is the part your language was built to hide — that memory is one array of
bytes and everything in it has an index — and then the assumptions that stop holding when there is
no runtime underneath you. [Chapter 1](#ch01) is the on-ramp; [chapter 2](#ch02) is the unlearning;
[chapter 3](#ch03) sorts C's constructs by a single question, *has the machine heard of this?*

**You do not need OS internals.** That is Part IV, and it is the point of using a kernel small
enough to read rather than one that has to be described.

**You do not need any hardware background.** Earlier drafts of this page asked for digital logic
and a pipeline diagram. Nothing in the book actually relies on either — [ch24](#ch24) builds the
pipeline from nothing, because a reader who has seen a five-stage diagram in a lecture still has
no idea what a real core does with a branch — so the requirement has come out.

### If you come from a managed language

Java, C#, Go, Python — the traps are the same, and they are traps rather than gaps. You are not
missing a concept; you have a correct one that means something else here.

| You already know | Here it is | Where |
|---|---|---|
| A reference | An index into one array of bytes, with a type saying how wide a step is | [ch01](#ch01) |
| `new`, and a collector | A fixed array decided at compile time, or a free list built out of the free memory | [ch02](#ch02) |
| An exception | A returned value the caller is expected to look at, and sometimes no way to report at all | [ch02](#ch02) |
| `volatile`, meaning *ordered between threads* | `volatile`, meaning *do not remove this access* — and **not** a threading primitive | [ch03](#ch03), [ch17](#ch17) |
| A JIT that optimises what runs hot | A compiler that optimised once, and a listing you can read | [ch09](#ch09), [ch23](#ch23) |
| A language memory model | Two hardware memory models, neither of which is your language's | [ch17](#ch17), [ch25](#ch25) |

The `volatile` row is the one that costs people afternoons. The keyword is spelled the same and
does a different job, and [ch03](#ch03) shows the compiler obeying the C one, instruction by
instruction.

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

## What you will be able to do

Concretely, and these are the things the problems make you do rather than read about:

- Take a duration on a real machine and say whether it means anything — what the clock cost, how
  many repetitions, which statistic, and what the measurement could not see.
- Read the disassembly of a function you wrote and account for what the compiler did with it.
- Stop a kernel in the middle of a trap and say what state is where, and why it had to be saved.
- Find the expensive part of a program you did not write, and know when the profiler is lying to
  you about which line it is.
- Predict a cost from a model before measuring, then say what the gap between the two means.

What you will not get is a list of numbers to remember. The reference machine's figures are this
machine's, and every chapter says so. The transferable part is the method.

## How the book is arranged

| | |
|---|---|
| **[Part I](#ch01)** — C, and what the machine does with it | Three chapters, and which of them you need depends on where you are starting. Not a C tutorial |
| **[Part III](#ch09)** — What a computer does with a program | One program from source text to result: the toolchain, representation, machine code, linking |
| **[Part IV](#ch13)** — The operating system layer | A kernel small enough to read, taken apart: traps, virtual memory, faults, drivers, locks, scheduling, files |
| **[Part V](#ch21)** — Where the cycles go | Part IV's chapters asked again as questions about time, on hardware that can answer them |

[Chapter 0](#ch00) sits before all of it and is setup: two targets working, and a script that
tells you what your machine can currently run.

The kernel Part IV reads has its own commentary @xv6-book, free from MIT and written by its
authors. It explains what that code does; this book asks what it costs. They go well together and
[Appendix G](#appendix-g) is the map — which of these chapters covers the ground of which of its
topics, and one system call traced through every layer it touches.

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
at anything. Parts III and IV live there.

The second is a small Linux machine on a desk, reached over SSH — a **Raspberry Pi 5** by
default. Every number in Part V is measured on it, natively. Not in an emulator, not on the
laptop, not extrapolated from a different machine.

The split is not a compromise; it is the argument. QEMU will happily answer a question about
nanoseconds and the answer will be meaningless, because it models no cache, no branch predictor
and no pipeline. Watching a program in a debugger tells you what it *does*. Only real hardware
tells you what it *costs*. [Chapter 15](#ch20) puts the same program through both and makes
the gap concrete.

### Why they do not share an instruction set

The kernel small enough to read in an afternoon is a RISC-V kernel. The hardware whose counters
actually work is an ARM one. Those are different machines, and pretending otherwise would mean
lying about one of them.

Part V needs `perf` to do two separate things: **count** events over a run, and **sample** —
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

Read down the columns. Choosing RISC-V for Part V would have made two of its eight chapters
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

**You get two memory models instead of one.** [Chapter 12](#ch17) teaches RISC-V's;
[chapter 20](#ch25) measures ARM's, which is also weak and differently specified. A reader shown only one would reasonably
conclude that model *is* memory ordering. Shown two, you learn it is a family, that a fence is an
architecture-specific spelling of an architecture-independent need, and that store buffers and
coherence are what actually transfer.

**[Chapter 15](#ch20) gets harder in the way that matters.** Three things differ between watching a program
under xv6 and profiling it on real hardware: emulation against hardware, one kernel against
another, one instruction set against another. Attributing a difference to the wrong one is the
commonest way to be confidently wrong about performance, and that chapter is where you practise
separating them.

Reading disassembly is a small part of the book, and this is the whole of what the split costs
you. In Parts I and II it is RISC-V: [ch01](#ch01), [ch03](#ch03), [ch09](#ch09), [ch10](#ch10) and
[ch11](#ch11). In Part V it is AArch64: [ch23](#ch23), [ch24](#ch24) and [ch28](#ch28).
[Chapter 0](#ch00) shows one small function compiled both ways, so the difference is concrete
rather than promised, and [Appendix F](#appendix-f) is a translation between the two for the
reader who meets the second having learned the first. Everything else is method, and method
does not have an architecture.

### One argument, not two tutorials

**Part V is not a second book. It is Part IV's chapters asked again as questions about time.**
Every chapter in it names the earlier chapter whose cost it measures, in its own header:

| When Part V asks | You already learned the mechanism in |
|---|---|
| [ch22](#ch22) — where is the data, and what does each step out cost? | [ch10](#ch10) layout and alignment, [ch14](#ch14) address translation |
| [ch23](#ch23) — what did that cost? | [ch11](#ch11) what the compiler emitted |
| [ch24](#ch24) — what is the core doing between fetch and finish? | [ch11](#ch11) the instructions themselves |
| [ch25](#ch25) — what do four cores cost each other? | [ch17](#ch17) locks, fences and ordering |
| [ch26](#ch26) — what does Linux charge for this? | [ch13](#ch13) traps, [ch15](#ch15) faults, [ch18](#ch18) switches |

So you never arrive at a Part V chapter cold. You arrive knowing the mechanism completely and
needing only the price — a better position than either half could put you in alone, and the reason
the book is arranged this way rather than as theory followed by benchmarks.

Three Part V chapters have no counterpart, deliberately: [ch21](#ch21) teaches measurement
itself, [ch27](#ch27) is about the whole machine rather than any one mechanism, and
[ch28](#ch28) concerns hardware Part IV never had reason to describe.

## How the numbers work

The stamped result behind each figure is a JSON file under `bench/results/`, and it records the
target, the board or QEMU version, the kernel, the compiler, its flags, and a hash of the code
that produced the number.

The consequence worth stating plainly is what happens when a machine cannot answer a question at
all. The chapter says so, shows the reasoning it used instead, and does not quietly substitute a
number from somewhere else. Five chapters depend on something specific about the reference
machine, and each says so in its own header rather than letting you discover it two hundred pages
in.

## What you will need

A laptop for Parts I, II and III — everything there runs under emulation, free. For Part V, a small
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
