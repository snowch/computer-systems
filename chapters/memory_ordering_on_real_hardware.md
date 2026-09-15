---
title: "Memory Ordering on Real Hardware"
short_title: "26 · Memory Ordering on Real Hardware"
---

(memory-ordering-on-real-hardware)=
# 26 · Memory Ordering on Real Hardware

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Answers the cost of** | [ch18](#locks-and-memory-ordering) |
| **Prerequisites** | [ch25](#the-cpu) |
| **Assumes** | Four cores and this interconnect's coherence. The scaling curve moves elsewhere; the mechanism does not. |
| **What it measures** | Which counters share a cache line: `bench/results/sharing-layout.json` |
:::

## The question

What do four cores cost each other, and what does a fence actually buy?

[ch18](#locks-and-memory-ordering) established what a lock is made of and said plainly that what it *costs* is
contention, which that target had no way to express. This is the chapter with four real cores, and
it is also the chapter where the reader meets a second memory model — which is not a repetition of
the first and is the reason this book has two architectures.

## The material

### A cost with no data in it

Two threads, two counters, no shared data and no race. One of the two arrangements below is
several times slower than the other.

```{include} _generated/memory-ordering-on-real-hardware-layout.md
```

The counters are the same counters. What differs is padding, and therefore whether the two land on
the same cache line — which is decided before anything runs, by the compiler and the layout, which
is why this figure is measured here rather than on the board.

Coherence works in lines, not in variables. When one core writes a line, every other core's copy
of that line is invalidated, and a core that wanted a *different* variable on that line has to
fetch it back. Neither thread is sharing anything; they are fighting over a container that happens
to hold both their things.

**False sharing is the name, and the name is slightly wrong in a useful way.** The sharing is
real — the line is genuinely shared — and what is false is the implication that the program meant
to share anything.

```{include} _generated/memory-ordering-on-real-hardware-sharing.md
```

Problem 18.1 is the analysis: given where the fields are and who writes them, which pairs will
contend. The case worth getting right is two fields on one line written by the *same* thread,
which costs nothing, because sharing a line is not the fault.

### The same need, two spellings

Now the second memory model, put beside the first on purpose.

[ch18](#locks-and-memory-ordering) printed what a release looks like on both architectures, and the two are not alike.
RISC-V emits `fence rw,w` and then an ordinary store: an instruction *between* the two things
being ordered. AArch64 emits `stlr` — a store that carries the ordering itself. One instruction,
no fence, and a reader who learned that a barrier is something you put between two operations will
not recognise it as a barrier at all.

Both satisfy the same requirement. Neither is the concept.

That is why this book uses two architectures, and it is worth stating as plainly as possible:
**a reader shown one weak memory model concludes that model is memory ordering.** Shown two, they
find that "weakly ordered" is a family; that a fence is an architecture-specific spelling of an
architecture-independent need; and that what actually transfers is the mechanism underneath —
store buffers, coherence, and the fact that another core can observe your writes in an order you
did not write them in.

Problem 18.3 is that correspondence as a table, and the table is not the point. The asymmetry is.

### What ordering costs

```{include} _generated/memory-ordering-on-real-hardware-atomics.md
```

Two columns because the difference between them is most of what there is to know. An atomic
operation on a line nobody else wants is nearly free: the core already owns the line exclusively
and the operation is local. The same operation on a line four cores are all writing costs the
coherence traffic to take the line away from whoever had it, every time.

So "atomics are expensive" is not a fact about atomics. It is a fact about contention, and the
same instruction has two costs that differ by a large factor depending on something that is not in
the instruction.

### Predict before you measure

[ch22](#measuring) asked for a distribution instead of a number. This chapter asks for something else
first: a **prediction**.

Amdahl's law says what a scaling curve can look like at best. If a quarter of the work cannot be
parallelised, four cores buy about two and a quarter times, and no number of cores buys four ever.
That is a ceiling computed from the program, before the machine is involved at all.

A measured curve on its own tells you very little. A measured curve that falls short of a
predicted one tells you there is something to find — and false sharing, atomic contention and
coherence traffic are exactly the things that live in the gap. Problem 18.2 is the prediction; the
board supplies the curve; the difference is the chapter's real subject.

## What we measured

Where the fields land, which decides whether the cores will fight, and which needs no machine.
The fights themselves are pending on the board, along with the cost of an atomic contended and
uncontended.

The runner refuses to stamp a layout in which the packed structure's counters have stopped sharing
a line or the padded one's have started, because either would leave this chapter demonstrating
nothing while still producing a table.

## What this cannot tell you

**Anything about a different interconnect.** The header says four cores and this coherence
fabric, and it means it. The scaling curve is this board's; the mechanism — invalidate on write,
fetch on read, in units of lines — is not.

**Whether your program has false sharing.** The analysis here is over a layout you can see. Real
programs share lines through allocators, through arrays of small structures handed one per thread,
and through padding decisions made in libraries. Finding it in something you did not write is
[ch28](#whole-machine-profiling)'s equipment.

**What the memory model permits.** This chapter measures what the machine *does*, and a weak
memory model is a statement about what it is *allowed* to do. Those are different, and the
difference is dangerous: a reordering that never happens on this chip may be permitted, and code
that relies on not seeing it is broken on a chip that does. [ch18](#locks-and-memory-ordering)'s problem 10.2 is about
the permission, deliberately, and no measurement can replace it.

**The cost of getting it wrong.** Every fence in this chapter is correct. What an incorrect one
costs is not a number — it is a program that works for a year and then does not, on a machine
nobody has yet.

## Problems

Three, in `tests/memory_ordering_on_real_hardware/sharing.c`.

**18.1 — Which fields will two cores fight over?**
Given offsets and writers, count the contending pairs. Two fields on one line written by the same
thread are not one of them.

```bash
python3 -m pytest tests/memory_ordering_on_real_hardware/test_problem_1_pairs.py
```

**18.2 — What does the curve look like before you measure it?**
Amdahl's law, applied. Do this before the board reports: a prediction you fail to reach is
information, and a measurement with nothing to compare it against is much less.

```bash
python3 -m pytest tests/memory_ordering_on_real_hardware/test_problem_2_scaling.py
```

**18.3 — Same requirement, two architectures.**
Give the spelling each one uses. The table is small; the observation that one of them has no
separate instruction at all is the reason the problem exists.

```bash
python3 -m pytest tests/memory_ordering_on_real_hardware/test_problem_3_spelling.py
```

## Where to go next

The ARM architecture reference manual's memory-model chapter and the RISC-V unprivileged
specification's RVWMO chapter @riscv-isa-unprivileged are worth reading in the same sitting, in
either order. They describe the same kind of object with different vocabulary, and the
correspondence is much easier to see when the two are half an hour apart than when they are years.

[ch27](#the-os-layers-cost) returns to Part IV with the same equipment. Everything xv6 demonstrated structurally
— a system call, a page fault, a context switch — has a price on this machine, and the chapter
puts the two accounts side by side.
