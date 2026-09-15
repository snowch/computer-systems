---
title: "The Same Program on Both Targets"
short_title: "21 · The Same Program on Both Targets"
---

(the-same-program-on-both-targets)=
# 21 · The Same Program on Both Targets

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | both — `xv6` and `host`, the same source compiled and run on each |
| **Answers the cost of** | [ch12](#machine-level-code-on-riscv), [ch14](#traps-and-system-calls), [ch15](#virtual-memory) |
| **Prerequisites** | [ch20](#the-file-system) |
| **What it measures** | Everything the two targets agree about: `bench/results/bridge-both.json`, and the timing that is not among them |
:::

## The question

What does watching a program in a debugger fail to tell me about what it costs?

Twelve chapters have built a complete structural account of a machine. You can say what a program
compiles to, where its data sits, how its address space is built, what it costs the kernel to ask
for anything, and how many blocks a byte reaches the disk as. All of it was obtained on a target
chosen precisely because you can stop it anywhere and look.

None of it is a duration, and this chapter is where that stops being a caveat and becomes the
subject.

## The material

### One program, two routes

Here is a program small enough that Parts III and IV explain it completely.

An array of cells, each holding a number and the index of another cell. The chain visits every
cell exactly once. Two routes add up every number: one walks the array in order, and the other
follows the chain.

```{literalinclude} ../sysfs/include/sysfs/bridge.h
:language: c
:start-at: long sysfs_bridge_sequential(const struct sysfs_cell *cells, long count)
:end-before: long sysfs_bridge_chased
```

They add the same numbers in a different order and return the same total. Compiled for the xv6
target and for the reference machine, run on both, they agree:

```{include} _generated/the-same-program-on-both-targets-agreement.md
```

That table is worth reading as a statement of how much this book has established. The same source
produces the same answer on two machines with different kernels, different instruction sets and
different everything else — because [ch11](#representing-information) checked the data model matched, and because the
answer is a property of the arithmetic rather than of the machine.

### What the structure predicts

Now the instructions. RISC-V first:

```{include} _generated/the-same-program-on-both-targets-sequential.md
```

```{include} _generated/the-same-program-on-both-targets-chased.md
```

Read the loop bodies. The sequential route loads a value, advances a pointer by a constant, adds,
and branches. The chased route does the same and then loads again to find out where to go next,
and has to compute an address from an index rather than stepping.

So: one more load, and a shift and an add. Everything [Part III](#part3) and [Part IV](#part4) have to say about these
two functions is in that sentence, and it predicts that the chased route costs somewhat under
twice what the sequential one does.

**Hold on to that prediction.** It is the most that a complete structural understanding can offer,
it was arrived at correctly, and [Part V](#part5) exists because of how wrong it is.

### The number that is not here

```{include} _generated/the-same-program-on-both-targets-cost.md
```

Nothing is substituted for it. That box is what this book does instead of a plausible figure, and
this is a good place to say plainly why: a duration measured under QEMU would be a description of
the laptop that ran the emulator. The emulator has no cache to miss, no prefetcher to defeat, no
store buffer to fill, and no memory that takes time. It would produce a number, the number would
look like the others in this book, and it would mean nothing at all.

The chased route's whole cost is that each load has to finish before the next address is known.
That is a statement about a memory system, and the target that has taught you everything else in
this book does not have one.

### Three things differ at once

When the board does report, there is a trap waiting, and avoiding it is the skill the rest of
[Part V](#part5) is built on.

The two runs differ in **three** ways simultaneously. One is emulated and one is not. One is xv6
and one is Linux. One is RISC-V and one is AArch64. A difference in the measurement could be
caused by any of them, and the temptation — universal, and not confined to beginners — is to
attribute it to whichever is most interesting.

The fix is not care. It is design: **compare two configurations that differ in exactly one thing.**
xv6 under QEMU against Linux under QEMU isolates the kernel. Linux under QEMU against Linux on
hardware isolates the emulation. Linux on one board against Linux on another isolates the
instruction set. Nothing can be isolated by comparing the first of those with the last, and no
amount of statistics applied afterwards recovers what the design gave away.

Problems 13.1 and 13.2 are that move, mechanically, until it is automatic.

### What survives the crossing

It is easy to summarise the last twelve chapters as "structure transfers and cost does not", and
that is wrong in both directions.

**The instruction count is structural and does not transfer.** Two instruction sets do not emit
the same number of instructions for the same source — the table above shows they do not, for this
very program. A model built on counting instructions is a model of one compiler for one
architecture.

**The memory layout is structural and does transfer**, but not automatically: it transfers because
both targets are LP64 with the same alignment rules, which [ch11](#representing-information) measured rather than
assumed. A book that had chosen a 32-bit target for [Part III](#part3) would have had to say something quite
different here.

And one thing transfers that is neither: **the mechanisms themselves**. A page fault is a page
fault, a context switch saves the callee-saved registers, a log makes a group of writes atomic.
What changes across the crossing is every number attached to them, which is exactly why [Part V](#part5)
is arranged as [Part IV](#part4)'s chapters asked again.

## What we measured

The answer both routes compute, on both targets, and the instructions each compiles to on both
architectures — all of it reproducible, none of it a duration. The one figure this chapter is
actually about is declared pending and renders as a warning, because the reference machine has not
reported yet.

The chapter is written so that it reads correctly either way. What Parts III and IV predict about
these two functions does not depend on the measurement, and neither does the argument about
confounds; the measurement supplies the size of the error and not its existence.

## What this cannot tell you

**Everything the chapter is about.** That is the point and it is worth stating as a limitation
rather than as a rhetorical flourish: the central claim here — that a complete structural model
predicts the cost badly — is *argued* in this chapter and *demonstrated* in the next eight.

**Which of the three differences matters most.** Naming the confound is not separating it. Doing
that needs configurations this book does not ship: a Linux image for the RISC-V target, or a
second board. [ch22](#measuring) starts from the machine the book does have.

**Whether the structural model is useless.** It is not, and the chapter would be dishonest to
imply it. It predicts the answer exactly, predicts the layout exactly, and predicts which of two
programs does more work — which is often the question. What it cannot do is turn that into a
ratio, and knowing which questions your model answers is worth more than a better model.

## Problems

Three, in `tests/the_same_program_on_both_targets/crossing.c`. All three are graded against a table of six configurations that
the tests read for themselves, so there is no key to find.

**21.1 — What does comparing these two configurations isolate?**
All thirty-six pairs. A comparison isolates a variable only when it is the single thing that
differs; otherwise it confounds, and the pair this book's own two targets form confounds all
three.

```bash
python3 -m pytest tests/the_same_program_on_both_targets/test_problem_1_isolates.py
```

**21.2 — Which configuration would test this claim?**
Somebody says the difference is caused by the emulator, or the kernel, or the instruction set.
Given where you are, name the configuration that would settle it — or say that none of the six
will, which happens and is the right answer when it does.

```bash
python3 -m pytest tests/the_same_program_on_both_targets/test_problem_2_pair.py
```

**21.3 — Does this observation transfer?**
Six things you could observe about the program. Sorting them into structure and cost gets two of
them wrong.

```bash
python3 -m pytest tests/the_same_program_on_both_targets/test_problem_3_transfers.py
```

## Where to go next

[Part V](#part5). Every chapter of it names the earlier chapter whose cost it measures, and the first of
them is about the instrument rather than the machine: before measuring anything, [ch22](#measuring)
asks how you would know a measurement was wrong, which on a board that throttles under sustained
load is not a rhetorical question.

For the confound itself, Mytkowicz and colleagues @mytkowicz2009wrong is the paper to read — it
shows measured speedups appearing and disappearing according to the size of an environment
variable, which is a more alarming demonstration of this chapter's point than anything here.
