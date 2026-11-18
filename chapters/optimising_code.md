---
title: "26 · Optimising Code"
short_title: "26 · Optimising Code"
---

(optimising-code)=
# 26 · Optimising Code

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `host` — native Linux on real hardware |
| **Answers the cost of** | [ch14](#machine-level-code-on-riscv) |
| **Prerequisites** | [ch25](#the-memory-hierarchy) |
| **Evidence** | Compiler output and native timings for five versions of a loop. |
:::

## The question

What will the compiler do for me, and what will it never do?

[ch25](#the-memory-hierarchy) ended by saying that what a memory access costs depends on what else
the machine could do at the same time. Given that, what is worth changing in the source? Start with
the changes the compiler is going to make anyway.

(optimising-code-example)=
## Compare compiler output for five loop variants

### Five ways to write one loop

`sysfs/lib/loops.c` contains the same loop five times. All five compute the same result from the
same input; they differ in which hand-optimisation has been applied.

The plain version recomputes a bound each time round and multiplies in the body. The hoisted
version lifts the bound into a local. The reduced version replaces the multiply with an addition —
strength reduction, done by hand. The unrolled version does four iterations per pass. And one does
all three at once.

That is the list a careful programmer reaches for when they do not trust the compiler. Here is
what the compiler made of it:

```{include} _generated/optimising-code-variants.md
```

### Three of them were the same program

Compare the plain, hoisted and reduced rows in the `-O2` column. The recorded compiler emits
the same number of instructions for these three variants. That count is evidence about the
size of these compiled functions. Use the native timing table below to compare the cost of
running them.

Compare the same rows under `-O0`. Different instruction counts at that level tell you how
these variants compile with optimisation disabled. Test with the flags your application will
use before relying on a benefit.

### And one of them backfired

Now the unrolled rows. At `-O2` the hand-unrolled loop is not shorter than the plain one. It is
substantially longer, and at `-O3` the gap widens rather than closes.

The hand-unrolled version has more compiled instructions with the flags in this table. The
compiler's transformations depend on the loop shape and flags. Check **Measured** in the native
timing table before attributing a runtime cost to a longer listing.

Use this comparison to decide which changes are worth carrying into a benchmark. Changes to
the data layout, algorithm or access pattern can also change what the processor has to do.
[ch25](#the-memory-hierarchy) gives examples from the memory hierarchy.

### The benchmark that measured nothing

A compiler this good will delete work that nothing observes, including the work a benchmark exists
to time — and then every number that benchmark reports is meaningless.

`tests/optimising_code/escapes.c` contains five functions doing identical arithmetic. They differ only in
what becomes of the result: dropped, returned, stored through a `volatile`, stored to a variable
outside any function that nothing reads, or used in a condition that is never true.

Two of those loops are removed entirely and three survive, and which is which is not the division
most people expect. Problem 26.3 is that prediction, graded by compiling the file and counting —
so the answer comes from a compiler rather than from this chapter's opinion.

The rule underneath is simple to state and easy to get wrong in practice: a compiler may remove
work whose result **nothing can observe**. Returning it counts. Storing it through a `volatile`
counts, which is [ch05](#c-for-people-who-will-read-a-kernel)'s keyword doing the job it exists for. Storing it somewhere nothing
reads does not count, however much it looks like it should.

A benchmark whose work has been removed does not report zero. It reports a very small number, and
a spectacular speedup, and nothing about it looks wrong.

### What this cost

```{include} _generated/optimising-code-cost.md
```

Instruction counts say whether a source change survived the compiler. They do not say what the
surviving differences cost; the board does. Read this table against the one above it. The three
variants that compiled to the same program cost the same, as they must. The two longer programs
cost more — and by a margin far smaller than the difference in their instruction counts would
suggest. That gap between the count and the cost is [ch27](#the-cpu)'s subject, and the reason
this chapter has claimed only what the counts can support: more instructions can run in nearly
the same time.

## What we measured

Instruction counts for five variants at three optimisation levels, on the reference architecture,
compiled and counted rather than run. CI regenerates them on every push, so the chapter's claims
about what this compiler does are checked against this compiler continuously — and if a future
version stops equalising those three, the build fails rather than the book quietly becoming wrong.

The timings are a different question, and the board answered it: the table under *What this
cost* is the same five variants at `-O2`, run rather than counted.

## What this cannot tell you

**Whether fewer instructions is faster.** It very often is not, and [ch27](#the-cpu) is the chapter
with the equipment to say why. Instruction count is the wrong unit for the final answer and the
right unit for *this* question, which is whether the source change survived at all.

**Anything about a different compiler.** Every claim here is about one compiler at three named
levels, recorded in the conditions line. A different one may equalise a different set, and the
method — compile the variants, count, compare — is what transfers.

**Where the algorithmic wins are.** This chapter is entirely about local transformations, because
those are the ones the compiler competes with you on. Nothing in it would tell you that a
different data layout removes most of the work, which is the change that usually matters and the
one no compiler will make.

**Whether `-O3` is worth it.** The table shows `-O3` producing more instructions than `-O2` for
two variants and the same for three, and says nothing about which runs faster. `-O3` trades size for
speculation about what will help; whether the trade pays is a property of the program and the
machine together.

## Problems

Use the files below in your local checkout. Run each test command from the repository root.

**26.1 — Which variants does the compiler equalise?**
Open `tests/optimising_code/problem_1_equalised.py`. Fill in `EQUALISED_AT_O2` with the groups
of versions that you predict compile to the same instructions. Give your prediction before
looking at the recorded comparison.

**26.2 — Which hand-optimisation backfired, and what does `-O3` do to it?**
In the same stub, fill in `BACKFIRED` and `BACKFIRED_AT_O3`. Identify the version with a
higher instruction count than the plain loop and say what happens at `-O3`. Run one command
for both predictions and compare with the captured AArch64 listings.

```bash
python3 -m pytest tests/optimising_code/test_problem_1_equalised.py
```

**26.3 — Which benchmark loops survive the compiler?**
Open `tests/optimising_code/problem_3_escapes.py`. Fill in `SURVIVES` to predict which
compiled functions still contain the loop. Read the candidates in
`tests/optimising_code/escapes.c`. The test builds and disassembles each one.

```bash
python3 -m pytest tests/optimising_code/test_problem_3_escapes.py
```

## Where to go next

Read the `-O2` and `-O3` sections of your compiler's own documentation — `gcc(1)` lists exactly
which passes each level enables, and it is a shorter and more useful document than its length
suggests. The two entries worth finding are the ones that name the transformations problems 26.1
and 26.2 are about.

[ch27](#the-cpu) is the chapter this one keeps deferring to. Instruction counts cannot say whether
the longer program is the slower one, because a modern core does not execute instructions one at a
time, and the next chapter is about what it does instead.
