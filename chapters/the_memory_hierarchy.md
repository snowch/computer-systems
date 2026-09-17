---
title: "The Memory Hierarchy"
short_title: "25 · The Memory Hierarchy"
---

(the-memory-hierarchy)=
# 25 · The Memory Hierarchy

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Answers the cost of** | [ch13](#representing-information), [ch17](#virtual-memory) |
| **Prerequisites** | [ch24](#measuring) |
| **Assumes** | A particular cache hierarchy. The numbers are this board's; the method is not. |
| **What it measures** | The hierarchy, by asking the machine rather than reading its datasheet: `bench/results/hierarchy-host.json` |
:::

## The question

Where is the data, and what does each extra step out cost?

[ch23](#the-same-program-on-both-targets) left a prediction on the table: two routes over the same array, differing by one
load, so the structural model says the slower one costs somewhat under twice the faster. This
chapter has the equipment to say what actually separates them, and it does not start by
looking anything up.

## The material

### Measuring a cache instead of reading about it

A datasheet will tell you this machine's cache sizes. So will `/sys`. Neither is the same as
measuring them, and [ch00](#prerequisites-and-setup) states the reason as policy: a specification
is a claim about a product line, and a measurement is a statement about the silicon in front of
you.

The instrument is a **dependent pointer chase** — a cycle of pointers, each pointing at the next,
walked one at a time. That shape matters. It makes every load wait for the one before
it, so the machine cannot overlap them, and what comes out is one latency rather than a
throughput. A loop that walks an array with independent loads measures how many loads the machine
can have in flight at once, which is a real number and a completely different one.

The cycle is also deliberately not sequential. A prefetcher that recognises a pattern will fetch
ahead and answer a question nobody asked.

### The steps are the levels

Walk a cycle that covers more and more memory, and plot how long one step takes:

```{include} _generated/the-memory-hierarchy-levels.md
```

The curve is flat, then steps, then flat, then steps again. Nothing in the program changed between
those points except how much memory the cycle covers, so each step is the *working set* — the
memory the loop touches — ceasing to fit in something, and the size at which it steps is the size
of the thing it stopped fitting in.

Nothing else is needed to find the levels. The hierarchy is not inferred from a specification; it
is read off a curve the machine produced when it was asked.

Problem 25.1 is that reading, on synthetic curves whose answers are known by construction.

### The line is the unit

A second experiment, with the working set fixed and the gap between visits growing:

```{include} _generated/the-memory-hierarchy-line.md
```

Flat, and then it climbs. While several visits share a cache line the later ones are nearly free —
the first fetch brought them all — and each doubling of the *stride*, that gap, halves how many
share, so the cost climbs a step at a time rather than jumping once.

The naive reading is that the stride at which it first rises is the line size. On this machine that
reading lands *below* what the vendor publishes, because the sharing thins out gradually: the curve
is already moving before the last visit has a line to itself. That gap is what the vendor table below
shows. So read the curve knowing that, rather than trusting the first rise — but what the line
*explains* does not depend on reading it to the byte. Alignment and padding matter because memory
moves in lines, and a structure straddling two costs two fetches for one field, which is the
question [ch13](#representing-information) raised and could not settle.

Problem 25.3 turns that into arithmetic. The shape it asks about is a ceiling: the line effect gets
steadily worse as the stride grows and then can get no worse, because one line per visit is as few
as they can share. The measured curve does something past that point that the arithmetic cannot
account for — it climbs steeply, then falls back — so whatever moves it there is a second effect
sharing the axis. By then the stride has grown to a page and beyond, and translation is involved,
which the next section measures. Why the curve falls back again is not something this chapter can
say from this curve alone, and it does not guess.

### Translation has a cache too

[ch17](#virtual-memory) established that every address is a question answered by a walk through three levels
of page table. It did not say what happens when that walk is not cached, because that target has
no cache to not-be-in.

Touch one pointer per page, so the *data* comfortably fits in the last-level cache while the
*translations* stop fitting:

```{include} _generated/the-memory-hierarchy-reach.md
```

The reach of a TLB is its entries multiplied by the page size, and the second row is that product.
The third row was meant to put the last-level cache beside it, and on this board it cannot: the
levels curve above found no step for one. Set the reach against the vendor's figure for that cache
in the table below instead, and the two are the same size — so on this core the translations run
out at about the point the data does, not well before it, which is the textbook shape and not
this machine's. What survives is the mechanism. A program whose data fits in cache can still pay
for a page-table walk on every access once it touches more pages than the TLB holds, and
[ch17](#virtual-memory)'s three levels are then three more memory accesses. That is where the
walk stops being a structural fact and becomes a cost; how large a one, on a board where the two
limits coincide, is not something this experiment separates.

### Comparing the curve with the datasheet

Every number above came out of a curve. Only now is it worth looking anything up.

```{include} _generated/the-memory-hierarchy-vendor.md
```

Two columns that ought to agree, and are allowed not to. Where they differ the measurement is what
this book prints, for the reason the chapter opened with — the right-hand column describes a
product line and the left-hand one describes the chip that produced it. A disagreement is not an
error in either: it is the most interesting thing on the page, and the question to ask is
which column you would have believed if you had only had one of them.

Here they disagree twice. The measured line is a fraction of the vendor's, and the section on the
line said why the first rise lands early. And the curve's second step sits at the size the vendor
gives for the *last* level, not the second: the level between them, which the vendor lists at a
quarter of that size, produced no step of its own. At this instrument's resolution the curve could
not separate that level from the one behind it, so the measurement reports one step where the
datasheet lists two.

### Back to the two routes

Now the prediction can be judged.

[ch23](#the-same-program-on-both-targets)'s sequential route walks an array in order: every line is used completely before the
next is touched, the pattern is exactly what a prefetcher is for, and the loads do not depend on
each other, so the machine can have many in flight at once. Its chased route reads one pointer per
cell, in an order chosen to defeat prediction, and each load's *address* comes from the previous
load's *result* — so no amount of parallelism helps, and each step waits for a full latency at
whatever level the data happens to be at.

The structural model saw one extra load and predicted a factor under two. What separates them is
not the load count. It is that one program can overlap its memory accesses and the other cannot,
which is not visible in the instruction stream at all.

That is the lesson [Part V](#part5) exists for, in its general form: **the cost of a memory access
is not a property of the access. It is a property of what else the machine was able to do at the
same time.**

## What we measured

Latency against working-set size, latency against stride, and latency against the number of pages
touched — each a dependent chase, each reported as a minimum over repetitions for [ch24](#measuring)'s
reason, and each measured on the board.

The comparison with the vendor's figures is deliberate and the rule is stated in advance: where
they disagree, the measurement is what this book prints and the disagreement is what it discusses.

## What this cannot tell you

**Anything about a different machine.** This chapter's header says it assumes a particular
hierarchy, and it means it: every number here is this board's. What transfers is the method, the
shape of the curves, and the reasoning — which is why the problems are about reading curves rather
than about remembering sizes.

**How the cache decides what to evict.** The steps say how big each level is and say nothing about
associativity — how many places in the cache a given address is allowed to sit — or replacement
policy, both of which are measurable with more elaborate versions of the same instrument and
neither of which this chapter builds. A working set that fits but crowds into too few of those
places behaves like one that does not fit, and nothing here would distinguish them.

**What a write costs.** Every experiment reads. Writes have their own path — store buffers,
write-allocate policies, and the coherence traffic [ch28](#memory-ordering-on-real-hardware) is about — and measuring reads
and assuming writes behave similarly is a good way to be wrong by a large factor.

**Whether the prefetcher is helping.** The instrument is built to defeat it, on purpose, so that a
latency is a latency. That means every number here is a *worst case*, and a real program with a
predictable access pattern may never see any of them. [ch26](#optimising-code) is where making a pattern
predictable becomes a thing you do deliberately.

**Whether the largest working set reached main memory.** The levels curve stops stepping at the
last size tried, and nothing in it says whether that final plateau is a cache or the memory behind
it. A working set larger than every cache should step again, higher; the sizes tried here did not
show it, and the reason — a set still small enough, a pattern the prefetcher could follow after
all, or something else — is a question for the board rather than for this page.

## Problems

Three, in `tests/the_memory_hierarchy/hierarchy.c`, graded against curves the tests construct with known answers.

**25.1 — Where does the curve step?**
Four curves, including one that drifts upward without stepping. A threshold that calls that a step
finds levels in every machine, including ones that do not have them.

```bash
python3 -m pytest tests/the_memory_hierarchy/test_problem_1_steps.py
```

**25.2 — What is the line size?**
The stride at which consecutive visits stop sharing. One of the curves is flat throughout, and the
right answer there is that there is no answer.

```bash
python3 -m pytest tests/the_memory_hierarchy/test_problem_2_line.py
```

**25.3 — How many lines does this loop touch?**
The arithmetic behind the curve, including the ceiling: past one line per element, a larger stride
buys the machine nothing back.

```bash
python3 -m pytest tests/the_memory_hierarchy/test_problem_3_lines.py
```

## Where to go next

The BCM2712's documentation @rpi-bcm2712 and the Cortex-A76 technical reference manual
@arm-a76-trm give the figures this chapter measures. Read them **after** running the experiments,
in that order, and treat any disagreement as interesting rather than as an error — a datasheet
describes a design and a measurement describes a chip.

[ch26](#optimising-code) is the other half of this. Knowing where the data is tells you what a program costs;
the next question is what the compiler will do about it unasked, and what it will never do however
obvious it looks.
