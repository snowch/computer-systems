---
title: "Whole-Machine Profiling"
short_title: "30 · Whole-Machine Profiling"
---

(whole-machine-profiling)=
# 30 · Whole-Machine Profiling

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Prerequisites** | [ch29](#the-os-layers-cost) |
| **Assumes** | that `perf` can sample. ARM PMUs support counter-overflow interrupts as standard, so this works on the reference machine — but most affordable RISC-V cores do not, and a reader following [Part V](#part5) on one will find this the chapter they cannot run. |
| **What it measures** | What the program under the profiler does, counted before anyone times it: `bench/results/tally-census.json` |
:::

## The question

How do I find the bottleneck in something I did not write?

Every measurement in this book so far has been of code the book wrote, in a loop chosen to isolate
one mechanism, with the answer known before the machine was asked. That is the right shape for
learning what a cache is. It is the wrong shape for the only situation in which any of this gets
used, which is a program you did not write, doing something you do not fully understand, too
slowly.

## The material

### The program, and what it is about to do

`sysfs/tools/tally.c` reads a stream of records, turns each into a table index, and counts them.
That is the whole description you get, and it is deliberately more than you would usually have.

Before profiling it, write down what it does. Not what it costs — what it *does*, counted.

```{include} _generated/whole-machine-profiling-census.md
```

Three of those rows are worth staring at.

The keys do not reach every counter in the table, and yet they reach **every cache line in it**.
A line holds a run of adjacent counters, so the untouched entries buy nothing at all: misses are
counted in lines, and there are no unvisited lines. This is [ch28](#memory-ordering-on-real-hardware)'s observation about coherence reappearing as
an observation about capacity, and both are the same fact — the machine deals in lines, and your
data structure does not know that.

The conditional in the decode phase is taken almost every time. It is the most conspicuous thing
in the source of that function, and [ch27](#the-cpu) already established what a branch this lopsided
costs a predictor.

And the partitioned arrangement adds substantial extra traffic in re-reading the keys in order to shrink
the table in play at once. Whether that trade pays is not a question the census can answer. It is
the reason there is a second arrangement at all.

**The census is a prediction, and writing it down first is the method.** A profile with nothing
committed to beforehand is remarkably easy to agree with: whatever it blames becomes what you
expected all along, and the exercise teaches nothing. `bench/run_profile.py` refuses to stamp a
census in which the two arrangements stop computing the same answer, or the scattered pass stops
reaching every line, or the conditional stops being lopsided — because any of those would leave
the chapter pointing confidently at the wrong phase.

### What a profiler actually does

```{figure} _figures/whole-machine-profiling-sampling.svg
:alt: A cycle counter overflowing into an interrupt, the PC written down, and the loop where the instruction blamed is not the instruction that waited.
:width: 100%

The address written down is the one the core had reached when the interrupt arrived, and not the
one that was waiting.
```

Nothing watches your program. A counter in the PMU is set to a large negative number, the core
counts cycles into it, it overflows, and the overflow raises an interrupt — which is
[ch19](#interrupts-and-drivers)'s mechanism, in hardware you have already met, doing a job that has nothing to do
with a device. The handler writes down where the program was and returns. Later, addresses are
matched against symbols.

Everything a profile can and cannot tell you follows from those sentences.

It is statistical, so a symbol holding a small share of the time has a count that is mostly noise
— problem 30.2 is how many samples a claim needs before it is worth making, and the answer is
often more than the profile you are looking at contains.

It is attributed to an address, so what you get is *exclusive* time: the samples that landed in
each function itself. The symbol at the top of that list is very often a leaf you did not write
and cannot change. Problem 30.1 is putting the callers back together, and the reason it matters is
that the thing you can change is never the leaf.

And the address written down is the one the core reached when the interrupt was taken, which is
not the one that was waiting.

### Skid, and why the line is a lie

```{include} _generated/whole-machine-profiling-scatter.md
```

The inner loop of the scattered pass is a handful of instructions, and the census has already
told you which one will stall: the second load, the one indexed by the key, reaching into a table
far too large to sit in cache. The load after it and the store after that cannot proceed until
it returns.

The stall is real and it belongs to that load. The *sample* lands somewhere after it, because the
interrupt is taken when the machine notices, and by then the program counter has moved on.

```{include} _generated/whole-machine-profiling-skid.md
```

So the rule for reading a profile at instruction granularity is to read the neighbourhood and
never the line. An instruction with no reason to be expensive, sitting immediately after one with
every reason, is not a mystery. It is the shape of the measurement.

### The artefact that is worse than noise

There is a second way a profile misleads, and unlike skid it leaves no trace.

A profiler sampling at a fixed period, over a loop of fixed length, does not sample the loop
evenly. The sample positions walk around the loop in steps of the sampling period, and that walk
does not visit every position — it visits the multiples of a number that problem 30.3 asks you to
find. When the two periods share a large factor, the profile lands on a handful of positions out
of thousands, every time, on every run, reproducibly.

This is worse than a noisy profile, because a noisy profile looks noisy. An aliased one looks
like a finding. It is stable across runs, it is consistent between machines with the same timing,
and it will tell you with great confidence that one instruction in a loop is responsible for
everything.

The fix is not to choose the period more carefully; there is no period that is coprime to every
loop. It is to make the period slightly random, which real profilers do, and which is worth
knowing about because it is the reason the tool's defaults are not round numbers.

### Before and after

```{include} _generated/whole-machine-profiling-profile.md
```

The change is the second arrangement: partition the keys so that every increment lands in a slice
of the table small enough to stay resident, at the cost of reading the keys twice more and writing
them once more.

Two outcomes are worth distinguishing, and the chapter commits to neither in advance. If the
program got faster, the census explained why before the profiler did, and the trade — more traffic
for better locality — is one you can now look for elsewhere. If it got *slower*, that is the more
valuable result: the profile moved, the symbol it blamed changed, and the program did not improve,
which is precisely what happens when you optimise what the profile blames rather than what the
measurement says.

## What we measured

The census: what the program touches, counted, in units that do not depend on any machine. CI
re-runs it on every push and refuses three specific ways it could stop describing the chapter.
Alongside it, the disassembly of the scattered inner loop, which is what makes the skid discussion
concrete rather than a warning.

Measured on the board: the profiles themselves, before and after, and the instruction-level samples
that show where the skid put them.

## What this cannot tell you

**Where the time goes in a program that is not CPU-bound.** Sampling on cycles finds code that is
executing. A program waiting on a disk, a socket or a lock is not executing, and a cycle-sampled
profile of it will be a beautifully detailed picture of the small part that was. The counters for
that are different ones and the tooling is a different chapter.

**Anything about a machine whose PMU cannot interrupt.** The header says this and means it. The
counting parts of `perf` work on far more hardware than the sampling parts; the census in this
chapter was designed to be useful to a reader in that position, and the profile cannot be.

**Whether the symbol is the cause.** A profile is a map of where time was spent, which is a
different question from what is responsible for spending it. The scattered pass is expensive
because of a decision made in the decode phase about how keys are distributed, and no amount of
sampling inside the loop points at that.

**How to profile something that is fast.** Every technique here needs the program to run long
enough to collect samples. For anything shorter, the equipment is [ch24](#measuring)'s — repetition and
a distribution — and the two do not substitute for each other.

**What it costs to measure.** The interrupt has to be taken, the handler has to run, and the
sample has to be written down. At a high sampling rate that is not free, and it is charged to the
program being measured. Nothing in this chapter tells you how much, because measuring the cost of
a measurement with the same measurement is circular.

## Problems

Three, in `tests/whole_machine_profiling/profiler.c`.

**30.1 — Flat to inclusive.**
Given a call tree and the profiler's exclusive counts, work out what each function cost including
everything it called. The symbol you can change is never the one at the top of the flat list.

```bash
python3 -m pytest tests/whole_machine_profiling/test_problem_1_inclusive.py
```

**30.2 — How many samples is a claim?**
Derive the closed form for the number of samples a share needs before it is worth believing. It is
small enough to do in your head with a profile on the screen, which is the point of deriving it.

```bash
python3 -m pytest tests/whole_machine_profiling/test_problem_2_noise.py
```

**30.3 — Why the period is random.**
A fixed sampling period over a fixed loop visits only some positions. Work out how many, and the
reason real profilers jitter will follow from the formula rather than from being told.

```bash
python3 -m pytest tests/whole_machine_profiling/test_problem_3_aliasing.py
```

## Where to go next

`perf_event_open(2)` @perf-event-open is the interface everything in this chapter sits on, and it
is worth reading once even if you never call it: the structure it takes is a list of every
decision a profiler makes on your behalf. Mytkowicz and colleagues @mytkowicz2009wrong is the
paper to read on measurement bias — it shows profilers disagreeing with each other about the same
program, for reasons that are nobody's bug, and it is the best available argument for the habit
of writing the prediction down first that this chapter is built on.

[ch31](#vectors) is the last measurement in the book and the narrowest: one loop, one unit, and the
question of what vectorising actually buys when it is measured against the arithmetic rather than
against the version you started with.
