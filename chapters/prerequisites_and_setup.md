---
title: "Prerequisites and Setup"
short_title: "00 · Prerequisites and Setup"
---

(prerequisites-and-setup)=
# 00 · Prerequisites and Setup

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU, whose toolchain `bare` shares |
| **Prerequisites** | none |
| **What it measures** | That the emulated targets work, and exactly what they are: `bench/results/setup-xv6.json` |
:::

## The question

What do I need on my desk, and how do I know it works?

Knowing it works matters as much as having it. Every later chapter rests on a claim about a
machine — this compiler, this kernel, these counters — and a setup that is *almost* right fails
three chapters later as something that looks like a bug in the material. So this chapter ends with
a script that interrogates the machine you are sitting at and says which of the book's three
targets it can run, and with measurements that record what those targets actually are.

## The material

### Three targets, and what the repository does about it

The [preface](#preface) makes the case for the arrangement; here is what each target is in practice.

**`bare`** is `qemu-system-riscv64` with no kernel under it at all — the machine on its own.
[Part II](#part2) builds on it directly, and it shares xv6's cross-compiler and setup, so one
check covers both.

**`xv6`** is the MIT teaching kernel under `qemu-system-riscv64`: a complete operating system in
about nine thousand lines, which you can stop anywhere — halfway through entering the kernel, if
you like — and inspect. Parts I and IV live there, and so does everything the book says about
*what a program does*; [Part III](#part3) works on both sides of the split, and
[ch12](#what-a-computer-does-with-a-program) is where it crosses.

**`host`** is a small Linux machine on the desk, reached over SSH — a Raspberry Pi 5 in this book.
Everything about *what a program costs* is measured there, natively. [Part V](#part5) lives there.

QEMU is a functional emulator, and every later chapter depends on what that means. The
[preface](#preface) says so too: QEMU computes what the instructions compute and models nothing
else — none of the machinery that decides how long an instruction actually takes, so no cache, no
branch predictor, no store buffer, no pipeline, no memory latency. Ask it how long a loop took and
it will answer, and the answer describes the laptop QEMU was running on and how it happened to
translate the instructions.

Almost every convenient way to observe a program changes what you are observing. A debugger stops
it. A profiler samples it. A print statement in a loop makes the loop something else. Knowing
which of your tools is lying to you about which question is the discipline underneath all of this,
and it holds well beyond QEMU, which is why the book starts here.

So the repository enforces the split rather than trusting anyone to remember it. Every result
file records where it was measured, and `scripts/verify-numbers.py` rejects two things outright:
a `host` figure that was not produced natively on the hardware it claims, and an `xv6` result that
contains a duration at all.

```{literalinclude} ../bench/stamp.py
:language: python
:start-at: def provenance_problems
:end-before:     problems: list[str] = []
```

### What you need

Two machines, and only one of them has to be bought. Whatever you are reading this on runs both
emulated targets; `host` needs a small Linux board. The reference board is a **Raspberry Pi 5**,
but what matters is a capability rather than a part number: `perf`, Linux's tool for reading the
processor's performance counters, has to be able both to count events and to sample where the
program was when they happened. [Appendix H](#appendix-h) states that properly, and says how to
check a machine you already own and what changes if yours differs from the reference. Read it
before you spend anything — and then carry on here, because nothing in this chapter needs the
board.
[ch01](#setting-up-the-board) is where it gets set up, and twenty-two chapters go by before
anything depends on it.

### Setting up the xv6 target

On the Mac, via Homebrew:

```bash
brew tap riscv-software-src/riscv
brew install riscv-tools qemu
```

On a Debian or Ubuntu machine, including the board itself:

```bash
sudo apt install -y gcc-riscv64-linux-gnu qemu-system-misc qemu-user-static gdb-multiarch
```

`qemu-user-static` is worth installing even though no chapter requires it. It runs a program built
for a different processor directly on your own machine — an ARM binary on an x86-64 laptop, say —
which means every `host`-target example in [Part V](#part5) can be compiled and **checked for
correctness** away from the board. It cannot tell you anything about time, and the repository does
not let it try — but it is the difference between being able to work on [Part V](#part5) from a
train and not.

#### The repository

```bash
git clone --recursive https://github.com/snowch/computer-systems.git
cd computer-systems
python3 -m pip install -r requirements.txt -r requirements-dev.txt
```

`--recursive` matters: xv6 is a submodule, not a copy. If you have already cloned without it,
`make submodule` fixes it.

xv6 is MIT-licensed and copying it in would be perfectly legal, but a copy would hide what this
book changes about the kernel. So the submodule stays pristine — a test asserts that it is
byte-identical to upstream — and the book's own material is kept separately and combined into a
staging tree at build time:

```
xv6/xv6-riscv/   upstream, never modified
xv6/apps/        the book's xv6 programs
xv6/patches/     the book's kernel instrumentation, as diffs
xv6/stage/       generated: all three, combined
```

So `ls xv6/patches/` is a complete answer to "what has this book done to the kernel?", and that
answer stays true. `xv6/README.md` has the mechanics.

#### Booting it

```bash
make xv6-qemu
```

You should get a boot log, a shell prompt, and `ls` should list a couple of dozen programs.

**Getting out again is `Ctrl-A` then `X`.** It is a sequence rather than a chord: hold control and
press A, let both go, then press X. QEMU exits immediately.

The key belongs to QEMU rather than to xv6. xv6 has no way to halt the machine — no
`shutdown`, no `halt`, nothing — so there is nothing to type at the shell prompt that would end
the session. You are stopping the emulator out from under a kernel that has no opinion about it,
which is the first of many small reminders that this is a teaching kernel and not a product.

`Ctrl-A` then `C` switches the same terminal to QEMU's own monitor, where `quit` also exits and
`info registers` works without a debugger attached. `Ctrl-A` then `C` again switches back. Learn it
now rather than later: when [Appendix B](#appendix-b) has QEMU halted at reset waiting for a
debugger, the terminal looks frozen, and the monitor is how you confirm it is not.

The same thing non-interactively, which is how the tests do it:

```bash
python3 scripts/xv6-run.py -c ls -c sysprobe
```

### Running the book's programs

Every listing in this book is a real file that really compiles, and `./run` builds and runs any of
them on whichever machine it belongs to.

```bash
./run --list
```

```bash
./run firstc          # a host program: compiled and run here
./run trap            # bare metal: cross-compiled and booted with no operating system
./run sysprobe --target xv6
```

Use it constantly. Change a line in the source, run it again, see what moved — that loop is what
this book is asking you to do, and it is the difference between reading that a handler must
advance `mepc` and watching what happens when it does not.

`./run` never touches anything committed. The figures in the chapters come from `bench/run_*.py`,
which stamp a result and refuse one that has stopped demonstrating its chapter's claim; `./run`
just builds and runs, so experimenting is free and cannot corrupt a number.

### Checking the whole thing

```bash
python3 scripts/verify-setup.py
```

It reports each target separately, because most machines can run two of the three. On a laptop it
confirms the cross compiler, QEMU, the submodule and a usable debugger, then says that the `host`
target is read-only here — no figure can be measured on this machine — and whether a cross-built
correctness path is available. On the board itself it reads the device tree and `/proc/cpuinfo`,
prints whatever that kernel says identifies the core — an implementer and part number on ARM, an
ISA string and three implementation IDs on RISC-V — and checks that `perf` reaches hardware.

It looks nothing up. Every fact it prints is read from the machine in front of it. A specification
describes a product line; `/proc/cpuinfo` describes the silicon that is about to produce your
numbers, and when the two disagree — which happens — the book cites the one it measured.

#### The same program in both worlds

Two commands remain. The first boots the kernel, runs a probe and stamps this chapter's first real
result; the second builds the same probe for the other target and checks that the two agree about
every answer.

`sysfs/include/sysfs/probe.h` asks the machine a handful of questions it can answer without a
library: how big each basic type is, which addresses it is allowed to start at, what the compiler
does to a struct, and which end of a multi-byte value holds its least significant byte. It is compiled twice from the same bytes, for two targets
that disagree about what a C library is, and the header says so at the top — the first design
decision in this book that exists entirely because of where the code has to run:

```{literalinclude} ../sysfs/include/sysfs/probe.h
:language: c
:start-at: /* Facts the machine will tell you
:end-before: #ifndef SYSFS_PROBE_H
```

The rest of the header follows from that decision. Asking the machine which end of a value it
puts the least significant byte at, rather than assuming, costs three lines of C:

```{literalinclude} ../sysfs/include/sysfs/probe.h
:language: c
:start-at: /* Byte order, asked of the machine
:end-before: /* Byte offset of a member
```

Run it in both worlds:

```bash
make bench-xv6                                   # boots xv6, runs the probe, stamps the result
python3 -m pytest tests/test_xv6.py -q           # asserts the two targets agree
```

## What we measured

The xv6 target, described by a boot rather than by a claim:

```{include} _generated/prerequisites-and-setup-xv6-environment.md
```

The C implementation it presents, as reported from inside the kernel:

```{include} _generated/prerequisites-and-setup-probe-types.md
```

This is the **LP64** data model: `long` and pointers are 64-bit, `int` stays 32-bit, and every
basic type's alignment — the address boundary it has to start on — equals its size. That is a
choice made by the ABI, the agreement between compiler and operating system about how data is laid
out and passed around; RISC-V spells its variant LP64D, for the double-precision float convention
@riscv-psabi, and AArch64 arrives at the same layout by its own route. If you have only ever
worked on 64-bit Linux this will look like the way things are. It is a choice, made twice,
independently, and [ch13](#representing-information) takes it apart.

The third table matters most. Two structs, the same three members, different declaration order:

```{include} _generated/prerequisites-and-setup-probe-layouts.md
```

The compiler did not reorder them — C forbids it — so writing them in the order that happened to
occur to you cost bytes that hold nothing at all. On one struct that is an oddity. Across an array
of a few million of them it is the difference between fitting in cache and not, which is
[ch25](#the-memory-hierarchy)'s subject and the first place this chapter's dry table turns into a number of
nanoseconds.

## What this cannot tell you

Everything above is *structural*: sizes, offsets, byte order, which programs are in an image, how
many harts (independent hardware threads) announced themselves. Those are questions QEMU answers perfectly, because they are
questions about what the instructions compute.

None of them is a question about time, and that is deliberate rather than an accident of what this
chapter chose to measure. The xv6 target will never produce a timing in this book,
because a timing produced there would be meaningless, and a meaningless number in a table is
worse than a missing one — a missing number announces itself.

[ch01](#setting-up-the-board)'s table is the other half of the same discipline, and if it is
showing a warning box rather than numbers, that is because the measurement has not been taken
yet: nothing is estimated, interpolated, or carried over from a different machine. `make
bench-board` refuses to run anywhere but the board, and `scripts/verify-numbers.py` rejects the
result if it somehow arrives from anywhere else.

Three more limits worth naming now, since all three come up repeatedly:

**A correct answer is not a fast answer.** CI compiles every `host`-target example for AArch64
and runs it under user-mode QEMU. That proves the instructions are right and the answers are
right, and it proves nothing whatsoever about cost. When a chapter says a result was checked in
CI, it means checked, not timed.

**This machine is one data point.** Four out-of-order cores with a three-level cache is an
ordinary shape, not a universal one. Ratios and mechanisms generalise; absolute numbers do not,
and the chapters whose reading depends on this particular core say so in their own headers.

**And it is a machine that changes speed.** A Pi 5 throttles under sustained load, so a long run
can be measuring a different clock at the end than at the start. That is not a flaw in the board —
it is what most real hardware does, including the laptop you are reading this on, and a book that
measured on a machine which never throttled would be teaching you to ignore something that
matters. [ch24](#measuring) deals with it properly.

## Problems

Three, and each one has a test that passes only when you have solved it. There is no answer key
in the back of the book — which means there is no answer key to be wrong.

**0.1 — Which of these would you publish?**
`tests/prerequisites_and_setup/problem_1_trust.py` asks you to write one function: given a stamped result, decide
whether a duration measured under those conditions is one this book may print. Five cases are
waiting for it, and exactly one of them is publishable. Getting this right is the same skill as
reading someone else's benchmark and noticing what they measured it on.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_1_trust.py
```

**0.2 — Predict the padding.**
`tests/prerequisites_and_setup/problem_2_abi.py` shows you a struct with five members and asks for its size, its
alignment, and the offset of each member — *before* you compile it. The test then compiles that
struct for whichever architecture this machine can execute, runs it, and tells you where you were
wrong. The tables above give you the sizes and alignments of the scalar types; the rest follows
from one rule, and it is the same rule on both architectures.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_2_abi.py
```

**0.3 — Your first xv6 program.**
`tests/prerequisites_and_setup/ch00ping.c` is a program that prints nothing. Make `ch00ping 41` print `pong 42`. The
arithmetic is not the exercise: the exercise is the path from a file in a test directory, through
the cross compiler, into xv6's user library, onto a file system image, into QEMU, and out of a
shell. If any link in that chain is missing you want to find out now, not in [ch16](#traps-and-system-calls).

```bash
python3 -m pytest tests/prerequisites_and_setup -q          # all three, including the ones you have not solved
```

These tests are marked `problem`, and CI deliberately does not run them. What CI does
run is the scaffolding beside each one: that the puzzle compiles, that the kernel boots with your
file staged into it, that the problem is answerable. The book is responsible for handing you a
problem that works. Making it pass is yours.

## Where to go next

The RISC-V specifications are the primary sources this book cites for anything architectural: the
unprivileged ISA @riscv-isa-unprivileged for instructions, the privileged architecture
@riscv-isa-privileged for CSRs, traps and paging, the ELF psABI @riscv-psabi for the calling
convention and the data model measured above, and the SBI specification @riscv-sbi for how Linux
reaches the counters. They are readable, and reading a specification directly is a skill this book
would like you to acquire early — the habit of checking rather than remembering is most of what
separates a confident answer from a correct one.

For the reference machine, Raspberry Pi's own documentation @rpi-bcm2712 gives the SoC and its
cache hierarchy, and Arm's Cortex-A76 technical reference manual @arm-a76-trm gives the pipeline
and the PMU events [ch27](#the-cpu) reads. The RISC-V hardware [Appendix H](#appendix-h) argues against is
documented at @starfive-jh7110 and @sifive-u74 if you want to follow that thread. Either way the
caveat stands: where a document and a measurement disagree, the book prints the measurement and
says so.

The study behind that decision is @riscv-pmu-profiling, and it is worth reading even if you never
touch RISC-V — it shows what it takes to establish what a machine can actually do, rather than
what its documentation says it has.

The xv6 source @xv6-riscv-source is worth browsing before [ch12](#what-a-computer-does-with-a-program), without trying to
understand it. Its authors also wrote a commentary on it, which is excellent and whose structure
this book deliberately does not follow; if you want a second account of the same kernel
after [Part IV](#part4), that is the one to read.

Next is [ch01](#setting-up-the-board) if the board is on your desk, and
[ch02](#reading-a-listing) if it is not — nothing between here and [Part V](#part5) needs it.
Further on, [ch12](#what-a-computer-does-with-a-program) takes a single program and follows it
from source text to a result on both targets, and asks — for the first of many times — which parts
of that journey cost anything.
