---
title: "The CPU"
short_title: "27 · The CPU"
---

(the-cpu)=
# 27 · The CPU

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Answers the cost of** | [ch14](#machine-level-code-on-riscv) |
| **Prerequisites** | [ch26](#optimising-code) |
| **Assumes** | An out-of-order core (Cortex-A76) and its performance counters. An in-order core would make this easier to read; see [ch00](#prerequisites-and-setup). |
| **What it measures** | What the core is given to work with: `bench/results/pipeline-shapes.json` |
:::

## The question

What is this core doing between fetching an instruction and finishing it?

[ch26](#optimising-code) ended on a deferral: instruction counts cannot say whether the longer program is the
slower one. This is why. A modern core does not execute instructions one at a time in the order
they appear, and the two things it does instead — overlapping independent work, and guessing
which way a branch will go — are what decide the answer.

## The material

### The branch that was not there

This chapter set out to measure branch misprediction, and its first act was to fail.

`sysfs/lib/pipeline.c` contains a loop that counts how many values exceed a threshold, written
with an `if`. Compile it and look:

```{include} _generated/the-cpu-shapes.md
```

The `count_over` row has a branch **removed**. The compiler saw that both sides of the `if` were
cheap, and replaced the branch with a conditional increment — `cinc` on AArch64 — which computes
both outcomes and selects between them with no control flow at all. There is nothing left to
mispredict. A measurement of branch prediction on that loop would have produced a number, and the
number would have been about something else entirely.

That is [ch26](#optimising-code)'s lesson arriving one chapter later and biting this book: what you wrote and
what runs are different things, and the gap is exactly where a measurement goes wrong quietly.

**The fix is to make the branch un-removable**, which means putting something in the taken case
that the machine cannot speculatively not-do. A call will do it: the compiler cannot compute both
outcomes when one of them is "call a function that might do anything". `count_over_calling` is
that loop, it keeps its branch, and the runner refuses to stamp a result in which these two stop
differing.

Problem 27.1 asks you to predict which of the two keeps its branch, before compiling. The stub
says plainly that this book got it wrong.

### The same additions, four different amounts of parallelism

Now the four sums. They add the same numbers with the same number of additions, differing only in
how many running totals they use.

Read their instruction counts in the table above and notice that they go the wrong way: the
one-accumulator version is the **shortest** program. By [ch26](#optimising-code)'s measure it should be the
best one.

It is the slowest, and the reason is not in the instruction stream. With one accumulator, every
addition needs the result of the one before it, so the machine can only ever have one in flight
however many execution units it has. With four, four chains proceed independently and the core
can overlap them. The work is identical; what differs is how much of it can happen at once.

```{include} _generated/the-cpu-ilp.md
```

Problem 27.2 is the arithmetic: the critical path is each accumulator's share of the elements plus
the tree that combines them. It is worth doing, and it is worth noticing what the model then
predicts — that more accumulators are always better, right down to one element each. They are not,
and what stops it is nowhere in the formula: accumulators live in registers, there is a fixed
number of those, and past that point they spill to memory and [ch25](#the-memory-hierarchy) takes over.

### Guessing, and what a wrong guess costs

A core that wants to keep many instructions in flight cannot wait to find out which way a branch
goes. It guesses, proceeds, and — when the guess was wrong — throws away everything it did since.

```{include} _generated/the-cpu-branches.md
```

The cost of one mispredict is **derived**, not measured, and this chapter says so in the table
itself. Nothing counts nanoseconds-per-mispredict directly; what is measured is the time per
element at several predictability levels and the misprediction rate at each, and the cost is the
slope between them. A derived quantity is a fine thing to publish and a bad thing to publish
without the word "derived" next to it.

The predictor itself is a small saturating counter per branch, and problem 27.3 is simulating one.
The alternating pattern is the case that explains the design: a one-bit predictor gets *every*
branch of `TNTNTN` wrong, because it always predicts what happened last time, and two bits fixes
exactly that by requiring two surprises before it changes its mind.

### Counters that are not counters

One warning specific to reading a PMU, and it applies to every chapter after this one.

Some events a performance monitoring unit reports are counted by hardware. Others are computed
from the ones that are — `perf` will happily report an "IPC" or a "miss rate" that is a division
of two other counters, and a "stall cycles" figure that is a subtraction. Those are derived, they
inherit the error of both inputs, and on some cores they are documented as approximate.

The rule this book follows is the one the table above uses: say which. A number that is counted
and a number that is computed are both useful and they are not the same kind of thing, and the
difference matters most exactly when the numbers are surprising.

## What we measured

The shapes: how many instructions each variant compiles to, how many conditional branches survive,
and how many the compiler replaced with arithmetic. All of it compiler output, all of it
regenerated by CI, and enough on its own to establish this chapter's first finding.

The timings and the counter readings are pending. They need the board, and [ch24](#measuring)'s
discipline applies to every one of them.

## What this cannot tell you

**Anything about an in-order core.** The header says this chapter assumes an out-of-order one,
because that is what the reference machine has and because [ch00](#prerequisites-and-setup) explains at length why
the alternative could not be used. The consolation is real: every machine a reader is likely to
optimise reorders, so attributing cycles on a core that reorders them is the skill that transfers.

**How wide the machine is.** The accumulator experiment finds where adding chains stops helping,
which is a lower bound on the number of additions the core can retire at once and not the same as
knowing its issue width. The vendor's manual @arm-a76-trm has the figure; the measurement has the
consequence, and they answer different questions.

**Where the mispredicted work went.** A wrong guess costs the work thrown away, and nothing here
says how far down the pipeline it got before being thrown. That depends on the depth of the
pipeline, which is not directly observable at all and is inferred from exactly the kind of slope
this chapter labels "derived".

**Whether the compiler will do any of this for you.** [ch26](#optimising-code) established that it does the
local transformations better than you will. Breaking a dependency chain by adding accumulators is
a change to the *arithmetic* — a different order of additions — and a compiler may only do that
when told the reordering is permitted. Which is a flag, and a decision, and not the default.

## Problems

Three.

**27.1 — Which of these loops still contains a branch?**
Predict before compiling, and be graded against the compiler. The stub records that this book
predicted wrongly.

```bash
python3 -m pytest tests/the_cpu/test_problem_1_branchy.py
```

**27.2 — How long is the critical path?**
Each accumulator's share plus the combining tree. Then notice what the model predicts and what
actually stops it.

```bash
python3 -m pytest tests/the_cpu/test_problem_2_path.py
```

**27.3 — How many does a two-bit predictor get wrong?**
Simulate the saturating counter. The alternating sequence is the one that explains why two bits
and not one.

```bash
python3 -m pytest tests/the_cpu/test_problem_3_predictor.py
```

## Where to go next

The Cortex-A76 technical reference manual @arm-a76-trm has the pipeline description and the list
of PMU events, and its event table marks which are architectural and which are
implementation-defined — which is the distinction the last section of this chapter is about.

`perf list` on the board is the other half of that: it names the events this particular kernel and
this particular chip agree exist, which is a smaller set than the manual's and the one you can
actually use.

[ch28](#memory-ordering-on-real-hardware) takes the same machinery and adds a second core. Everything in this chapter assumed
one thread with the whole machine to itself; the next one is about what four of them cost each
other, and it is where [ch20](#locks-and-memory-ordering)'s fences finally get a price.
