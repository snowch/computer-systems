---
title: "Systems From Scratch"
short_title: Preface
---

(preface)=
# Systems From Scratch

A self-study book on computer systems and performance, in five parts and thirty-two chapters.
Learn how C becomes machine code, how an operating system runs a program, and how to measure
where that program spends time.

**[Start with prerequisites and setup](#prerequisites-and-setup)** to get the examples running
on your computer.

## Who it is for

You should be comfortable writing functions, loops and conditionals in another language, such as
Python or Java. The book introduces the C, operating system and processor concepts it uses.
[Part I](#part1) explains how to read compiler output and how C represents data in memory.

## How to use the book

The site and PDF show read-only source code, diagrams and recorded results. To run a program or
change an exercise, [set up your local copy of the repository](#prerequisites-and-setup), then use
the terminal and a text editor. Run the original version before you make an edit. Compare the
specific values the chapter asks about with your prediction.

In a **Problems** section, edit the named file and run the test command from the repository root.
The exercise checks your answer. The setup checks tell you whether tools are available and the
example can run. A test that skips has left an exercise or its setup unchecked.

[Download the whole book as a PDF](/systems-from-scratch.pdf).

(three-targets-on-two-machines-on-purpose)=
## Three targets on two machines

A *target* is the environment where the example runs or where the compiler prepares it to run.
QEMU emulates a RISC-V machine on your computer. Use it to inspect behaviour such as which
address a trap records. Measure elapsed time and hardware events on native Linux.

| Target | Where it runs | What to inspect |
|---|---|---|
| `bare` | RISC-V in QEMU, without an operating system | Processor behaviour, such as trap handling and address translation |
| `xv6` | The xv6 teaching operating system on RISC-V in QEMU | Kernel behaviour, such as how a system call reaches its handler |
| `host` | Native Linux, on hardware with working performance counters for timing experiments | Program costs, such as elapsed time, cycles or cache misses |

Native hardware runs its own machine instructions. QEMU runs translated instructions on the
computer that hosts it, so emulator timings cannot estimate the emulated processor's costs.
You can read every chapter with a browser or the PDF. Your computer can run the emulated
examples once [setup](#prerequisites-and-setup) passes. Before running the timing experiments,
[check a native Linux machine](#setting-up-the-board) against [Appendix H](#appendix-h).

The two emulated targets use RISC-V. The reference board uses AArch64, Arm's 64-bit instruction
set. [ch02](#reading-a-listing) shows both and [Appendix F](#appendix-f) translates between them.
You read AArch64 disassembly in [ch26](#optimising-code), [ch27](#the-cpu),
[ch29](#the-os-layers-cost), [ch30](#whole-machine-profiling) and [ch31](#vectors).

## How the book is arranged

| Part | What you do |
|---|---|
| [Getting started](#part0) | Check your tools and run a first program. Set up the board before collecting native timing measurements. |
| [Part I](#part1) | Read a compiler's instructions and relate them to C types, addresses and functions. |
| [Part II](#part2) | Follow traps, interrupts, address translation, system calls and process creation on an emulated processor. |
| [Part III](#part3) | Trace a C program through compilation, linking and loading. |
| [Part IV](#part4) | Follow the same mechanisms through the xv6 kernel. |
| [Part V](#part5) | Use timings and performance counters to study their costs on real hardware. |

The xv6 authors' book is a companion reference @xv6-book. [Appendix G](#appendix-g) maps its topics
to this book and traces a system call through the kernel.

(one-argument-not-two-tutorials)=
### How the performance chapters build on earlier chapters

| Performance question | Earlier mechanism |
|---|---|
| [ch25](#the-memory-hierarchy) — How much does it cost to reach data? | [ch13](#representing-information) for layout and alignment, [ch17](#virtual-memory) for address translation |
| [ch26](#optimising-code) — Which code changes alter the measured cost? | [ch14](#machine-level-code-on-riscv) for compiler output |
| [ch27](#the-cpu) — How does the processor execute instructions? | [ch14](#machine-level-code-on-riscv) for the instructions it executes |
| [ch28](#memory-ordering-on-real-hardware) — What happens when cores share memory? | [ch20](#locks-and-memory-ordering) for locks, fences and ordering |
| [ch29](#the-os-layers-cost) — What do operating-system services cost? | [ch16](#traps-and-system-calls) for traps, [ch18](#page-faults-as-a-feature) for faults, [ch21](#scheduling-and-context-switches) for switches |

[ch24](#measuring) explains how to design a measurement. [ch30](#whole-machine-profiling) samples
activity across the machine. [ch31](#vectors) measures instructions that work on several values
at once.

## How the numbers work

The conditions under each result identify the machine, compiler and source record. Use those
conditions to judge which comparisons apply to your run. An illustrative diagram shows a
mechanism. A recorded figure reports a particular run, and a pending figure identifies a
measurement still to be made. Check the chapter's **What this cannot tell you** section before
using a result to predict behaviour or costs elsewhere.

```{include} _build_stamp.md
```
