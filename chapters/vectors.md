---
title: "Vectors"
short_title: "31 · Vectors"
---

(vectors)=
# 31 · Vectors

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Prerequisites** | [ch30](#whole-machine-profiling) |
| **Assumes** | a vector unit — NEON on the reference core. This chapter became measurable when [Part V](#part5) moved to AArch64; on a RISC-V board without RVV 1.0 it reverts to reasoning about code the compiler emits but the hardware cannot run. |
| **What it measures** | Which of five loops the compiler widens, at three sets of flags: `bench/results/vectors-census.json`; and what the widening bought: `bench/results/vectors-host.json` |
:::

## The question

What does vectorising actually buy, and when will the compiler do it for me?

[ch30](#whole-machine-profiling) was about finding the expensive loop in a program nobody here has
read. This chapter is what you do to that loop once you have found it, and it asks the narrowest
question in the book: the unit can do four of these at once, so what became of the other three?

## The material

### Five loops, three builds

```{include} _generated/vectors-loops.md
```

Read the second column first. At the book's own optimisation level — the one every other listing
in this book was compiled at, and the one a reader building this code gets — **not one of these
loops is vectorised**. That is the first half of the answer to "when will the compiler do it for
me", and it is not a subtlety: the default is no.

At `-O3` two of them widen. At `-O3` with permission to change the answer, a third joins them. Two
never do, at any setting.

So that table holds four different reasons a loop is not vectorised, and only one of them is about
the optimisation level.

### The one that widens

```{include} _generated/vectors-scale.md
```

Independent elements, one multiply each, nothing carried between iterations. The `-O3` version
does four at a time: one load of a quad-word register, one multiply across four lanes, one store.

Look at what it cost. The function is several times longer. The widening is three instructions in
the middle, and everything else is getting there — checking whether the pointers overlap, working
out how many full vectors there are, and handling the elements left over at the end.

**That tail is the part worth carrying away.** A loop shorter than one vector gains nothing at all
and pays for all of that code, and a loop one element past a vector pays a whole scalar iteration
for it. Problem 31.1 is the arithmetic, and the shape it produces is a sawtooth rather than a
slope.

### The one that is refused, and why it is right

```{include} _generated/vectors-sum-f32.md
```

A sum of floats. `-O3` leaves it scalar. The same loop over integers, in the table above, widens
at `-O3` without being asked.

The difference is not in the loop and not in the compiler. **Integer addition is associative and
floating-point addition is not.** Widening a reduction means adding the numbers in a different
order — lanes accumulating independently, partials combined at the end — and a different order can
give a different answer. A compiler that did that on its own would be changing your program's
output to make it faster.

The third column grants exactly that permission. `-ffast-math` says the answer may change, and the
loop widens immediately, which is the proof that the refusal was never a limitation. Hold on to
this one: the last table in this chapter says what the permission bought.

Problem 31.2 is the disagreement itself. You write both orders, the test supplies an input where
they differ, and you compare the bit patterns. Being told that floating-point addition is not
associative is not the same as watching the two answers come out different.

### The two that never widen

```{include} _generated/vectors-running.md
```

Each element needs the one before it. Lanes run at the same time, and the second lane cannot start
until the first has finished — so there is nothing for the width to do, and no flag changes that.
This is [ch27](#the-cpu)'s dependence chain again, at a different granularity and with the same
conclusion.

The other refusal is the gather: the elements are independent, but their addresses are not known
until the indices have been loaded. A vector unit is fastest reading a run of adjacent memory, and
this loop has no run to read. It stays scalar at every setting in the table.

**A note on reading a listing for vector instructions.** Counting instructions that name a vector
register does not answer the question. This compiler uses a half-width vector form to make a
floating-point zero, so the loop the chapter calls impossible to widen contains an instruction
that looks like vectorisation and is not. `bench/run_vectors.py` counts only full-width forms, and
found this out by tripping over its own guard.

### What it bought

```{include} _generated/vectors-speedup.md
```

Each measured speedup sits beside the most its lane count could possibly have bought.

Read the two loops that never widen first, and then stop reading their last column. Their measured
speedup is about one, as it must be, since nothing changed — and the percentage beside it is
arithmetic rather than achievement: anything that did not move at all sits at a quarter of a
fourfold bound by definition. The column means something only for the rows that widened.

Of those, the one with independent elements and a multiply each got most of the way to its bound,
and the integer reduction got a good deal less — the partials still have to be combined at the
end, and that combining is not four-at-a-time work.

**Then the float sum, which is the finding.** It widened, under permission this chapter spent a
whole section justifying, and it bought nothing whatever: its measured speedup is one. The
compiler's refusal at `-O3` was correct, the permission that overrode it was granted, the
vectorisation happened — and the loop takes what it always took, because what limits it is not
arithmetic width. Getting a program's answers changed and its time not changed is the worst trade
in this book, and nothing in the census could have predicted it. Only the measurement did.

Compare each speedup with its bound, then. A speedup on its own invites you to be pleased with it;
as a fraction of the bound it makes you ask where the rest went — and the answer is a tail, or
memory, or a loop that was never the bottleneck to begin with. Problem 31.3 is that arithmetic,
and it deliberately does not clamp: a result over the bound means something other than the width
changed, and the comparison has stopped being between two versions of one loop.

## What we measured

Which loops the compiler widens and at what flags, counted from the disassembly, which needs no
machine and so is checked by CI on every push. The runner refuses a census in which nothing widens
at `-O3`, nothing further widens under `-ffast-math`, or the loop with the dependence acquires
vector instructions — each of which would leave the chapter asserting something its own evidence
had stopped supporting.

Measured on the board: what the widening actually bought, beside what it was allowed to buy. The
five rows include the two loops that never widen, which are there as a control — a loop that did
not change should measure as not having changed, and they do.

## What this cannot tell you

**What a different compiler does.** Every refusal in that table is this compiler's, at this
version. The reason behind one of them — reassociation changes the answer — is a fact about
arithmetic and will hold everywhere. The other two are judgements about cost, and a different
compiler is entitled to judge differently.

**What a wider or different vector unit does.** NEON is a fixed width. Scalable vector extensions
on both of this book's architectures express the same loops without a compile-time width, which
changes the tail arithmetic in problem 31.1 fundamentally rather than in degree. The reference
machine does not have one, so this book has nothing to say about it that would be worth reading.

**Whether to write intrinsics.** Nothing here is written in intrinsics, deliberately: a chapter
about what the compiler decides cannot be written in a notation that takes the decision away from
it. What that costs is that the book never shows you the ceiling — a hand-written version might
beat every row of the last table, and this chapter would not know.

**Whether any of this is where your time is going.** [ch30](#whole-machine-profiling) is the chapter for that, and
the order matters. A loop vectorised to a quarter of its scalar cost, in code holding a hundredth
of the running time, has bought you well under one per cent.

## Problems

Three, in `tests/vectors/lanes.c`.

**31.1 — What the tail costs.**
Speedup from a lane count and a trip count. The case to get right is the loop shorter than one
vector, which gains nothing and pays for all the code.

```bash
python3 -m pytest tests/vectors/test_problem_1_tail.py
```

**31.2 — The same numbers, two orders.**
Write the sequential sum and the lane-wise one, and watch them disagree. This is the refusal
above, reproduced rather than described.

```bash
python3 -m pytest tests/vectors/test_problem_2_reassociation.py
```

**31.3 — The speedup you were allowed.**
A measured speedup as a fraction of the arithmetic bound. Do not clamp it: the value over a
hundred is the one that tells you something.

```bash
python3 -m pytest tests/vectors/test_problem_3_bound.py
```

## Where to go next

The ARM architecture reference manual's Advanced SIMD chapter @arm-arm is the specification for
what those
instructions do, and the RISC-V vector extension @riscv-isa-unprivileged is worth reading beside
it for the same reason [ch28](#memory-ordering-on-real-hardware) put two memory models side by side: it solves the tail
problem in problem 31.1 by not having a compile-time width at all, and seeing one design makes the
other's choices visible as choices.

That is the last measurement in the book. [Appendix A](#appendix-a) collects the reference cards,
and the [preface](#preface) says what this book set out to make you able to do. The test is not whether you
remember any of these numbers, but whether, next time something is slow, the first thing you reach
for is a measurement.
