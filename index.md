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
machine that produced it — not to every machine of that model, and not to Arm or to computers in
general — and the line under each figure says which machine, which compiler and what day. What
carries to your machine is the method, and the list above is a list of methods.

## Who it is for

Someone who programs fluently — in a scripting language, or Java, or anything else with a
runtime underneath it — and who has never had a reason to write C or read a kernel.

**You do not need to know C.** Three of [Part I](#part1)'s four chapters teach it,
and none of them is a C tutorial: control flow, functions and operators are assumed from whatever
language you already use. They teach the part your language was built to hide — that memory is one
array of bytes and everything in it has an index — and then the assumptions that stop holding when
there is no runtime underneath you. [ch02](#reading-a-listing) comes first and is for everyone —
it teaches reading what the compiler produced, which every later chapter asks you to do. Then
[ch03](#memory-is-one-array) gets you on to that model; [ch04](#c-without-a-runtime) takes away
what the runtime was doing for you; [ch05](#c-for-people-who-will-read-a-kernel) sorts C's
constructs by a single question, *has the machine heard of this?*

**You do not need OS internals.** [Part IV](#part4) teaches them, and that is why the book uses a
kernel small enough to read rather than one that has to be described.

**You do not need any hardware background.** [Part II](#part2) starts at a bare machine and
adds one mechanism at a time, so nothing about the hardware is assumed before it is built.
[ch27](#the-cpu) does the same for the processor itself: a reader who has seen a textbook diagram
of one still has no idea what a real core does when the program reaches an `if`, and that chapter
starts from there.

### Where it leads

This book is an on-ramp to *Systems Performance*
@gregg-sysperf, which assumes you already know what a system call costs, what a cache miss
is, why a profiler can blame the wrong line, and what a context switch moves. This book teaches you
those things by measuring them on a machine you own.

What it deliberately does **not** cover, and what you should read that book for: tracing and BPF,
flame graphs, the network and storage stacks, containers and cloud, and observability across many
machines. There is no overlap to speak of. This is the layer underneath, and you should read it
first, because the tools in that book all report quantities — cache misses, faults, context
switches — whose meaning this book establishes.

## What this book is

Three things make it the shape it is.

**Every number in it was measured, and says where.** No figure is typed into the prose. Each one
comes from a *stamped result* — a small file in the book's repository, under `bench/results/`,
recording the machine, the kernel, the compiler and its flags, and a hash of the code that produced
the number — and a check fails if a quoted figure stops matching the code. Where a machine cannot
answer a question at all, the chapter says so and shows the reasoning it used instead, rather than
quietly substituting a number from somewhere else.

**Every problem is a test, and there is no answer key.** Each chapter ends with problems that are
stubs under `tests/`, with a test that passes only when you have solved it. Nothing in the
repository contains the answers — which also means there is no answer key to be wrong.

**Every chapter ends by saying what it could not show you.** A section called *What this cannot
tell you* is mandatory, and it is where the tools ran out — what could not be run, measured or
shown. It is usually the most useful part of the chapter.

:::{note} Where this book is
All thirty-two chapters are written, and all eight of the eight appendices. Every measurement has
been taken — zero figures are marked *pending* — and [Appendix C](#appendix-c), which lists what
the reference machine's processor can count, was generated on that machine, the only place the list
could honestly have come from.

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
basic mechanisms one at a time because a kernel presents them entangled — the first trap you meet in a
real one arrives with a process table, a scheduler and a lock already attached. [Part III](#part3)
is next because a kernel is a program, and you cannot usefully read one until you know what a
program is and who finishes what the compiler left undone; [ch15](#linking-and-loading) ends
with the kernel starting a program, which is where [Part IV](#part4) begins. [Part IV](#part4) puts the entanglement back, and
it turns out to be most of what an operating system is.

[Getting started](#part0) sits before all of it: [ch00](#prerequisites-and-setup) sets up
everything that runs on your own computer and gives you a script that says what it can currently
run, and [ch01](#setting-up-the-board) sets up the second machine, whenever it arrives.

[Part IV](#part4) reads a real kernel, and that kernel has a book of its own: *xv6: a simple,
Unix-like teaching operating system* @xv6-book, written by its authors and free from MIT. The two
do different jobs — it explains what the code does, this book asks what that costs — and they go
well together. [Appendix G](#appendix-g) lines them up by topic rather than by chapter number,
because its numbering moves between revisions. The same appendix traces one system call through
every layer it touches.

## Three targets on two machines, on purpose

Almost every book on this subject picks one target and lives with its limitations. This one uses
three, because *what does a program do* and *what does it cost* need different instruments.

```{figure} chapters/_figures/prerequisites-and-setup-targets.svg
:alt: The bare, xv6 and host targets side by side, with what each can and cannot answer.
:width: 100%

The division of labour. Every chapter declares which target it uses, and every figure records
which one produced it.
```

The three are `bare` (a RISC-V processor — RISC-V is an open processor design — emulated by
QEMU on your own computer, with no kernel on it at all), `xv6` (the MIT teaching kernel, running on
the same emulator), and `host` (a real Linux machine, a Raspberry Pi 5 by default);
[ch00](#prerequisites-and-setup) sets them up and says what each can and cannot answer. That is
three targets on **two machines**: the first two are both QEMU on the computer you are reading
this on, and need one cross-compiler between them — a compiler that runs on your machine and
produces code for a different kind of processor. Only the third has to be real.
[Part III](#part3) works on both sides of the split, and
[ch12](#what-a-computer-does-with-a-program) is where it crosses.

The split is not a compromise. QEMU will happily answer a question about
nanoseconds and the answer will be meaningless, because it models no cache, no branch predictor
and no pipeline. Watching a program in a debugger tells you what it *does*. Only real hardware
tells you what it *costs*. [ch23](#the-same-program-on-both-targets) puts the same program through both and makes
the gap concrete.

The two emulated targets are RISC-V and the board is ARM, because the kernel small enough to read
is a RISC-V kernel, and the hardware whose performance counters actually work — the processor's own
tally of what it did, which is what every cost in this book is read from — is an ARM one.
[Appendix H](#appendix-h) has the evidence.

That costs you one thing: you read disassembly in two instruction sets rather than one. Five
chapters read it as AArch64, ARM's 64-bit instruction set — [ch26](#optimising-code), [ch27](#the-cpu),
[ch29](#the-os-layers-cost), [ch30](#whole-machine-profiling) and [ch31](#vectors) — and five read
it as RISC-V, in Parts I and III. [ch02](#reading-a-listing) shows one small function both ways
before either matters, and [Appendix F](#appendix-f) translates between them.

It also buys something. Two chapters are about how one processor core's writes to memory become
visible to another — [ch20](#locks-and-memory-ordering) on RISC-V and
[ch28](#memory-ordering-on-real-hardware) on ARM — and a reader shown only one of them would
reasonably conclude that is how it works everywhere. Shown two, you learn which parts are that
design's and which are the idea.

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

The chapters whose reading depends on something specific about the reference machine say so in
their own headers rather than letting you discover it two hundred pages in.

## What you will need

A laptop for [ch00](#prerequisites-and-setup) and for Parts I to IV — everything there runs under
emulation, free. A small Linux machine with working performance counters for
[ch01](#setting-up-the-board) and [Part V](#part5); a Raspberry Pi 5 is the reference, and one you
already own may well do — [Appendix H](#appendix-h) says exactly what it has to be able to do and
how to check. Twenty-two chapters sit between needing the first and needing the second.

And the book's repository. Every program a chapter shows, every problem it sets and every result
behind a figure is a file in it, and the book is meant to be read here and worked through in a
checkout — [ch00](#prerequisites-and-setup) starts by cloning it.

The book does not tell you which kernel to run. Whether a machine's performance counters work is
a property of its whole configuration — silicon, device tree, kernel, firmware — rather than of
the board, and the reference board's own counters went missing for a kernel release. So every
figure records the image and kernel that produced it, and
[ch00](#prerequisites-and-setup) hands you a script that asks your machine instead of a version
number to match.
