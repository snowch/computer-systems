---
title: "Optimising Code"
short_title: "ch23 Optimising Code"
---

(optimising-code)=
# ch23 · Optimising Code

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Answers the cost of** | [ch11](#machine-level-code-on-riscv) |
| **Prerequisites** | [ch22](#the-memory-hierarchy) |
| **What it measures** | What the compiler makes of five hand-optimisations: `bench/results/loops-aarch64.json` |
:::

## The question

What will the compiler do for me, and what will it never do?

[ch22](#the-memory-hierarchy) ended by saying that a memory access costs what it costs because of what else the
machine could do at the same time. This chapter asks the question that follows immediately: given
that, what is worth changing in the source — and the first thing to establish is which changes the
compiler is going to make anyway.

## The material

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

Read the `-O2` column first. **Plain, hoisted and reduced compile to identical numbers of
instructions.** The compiler hoisted the bound. The compiler reduced the strength of the multiply.
Both hand-optimisations were correct, both were unnecessary, and the code they produced was the
code the compiler was going to produce from the obvious source.

This is the most common thing that happens when people optimise C by hand, and it is worth being
precise about what it costs. Not run time — those three are the same program. What it costs is
that the source is now harder to read, harder to change, and no faster, and that a reader who
does not know this will preserve the hand-optimisation through every future edit because it looks
load-bearing.

At `-O0` they are not identical, which is worth noticing too: the hand-optimisations *do*
something to unoptimised code. Measuring at `-O0` and concluding that a transformation helps is a
reliable way to make a program worse.

### And one of them backfired

Now the unrolled rows. At `-O2` the hand-unrolled loop is not shorter than the plain one. It is
substantially longer, and at `-O3` the gap widens rather than closes.

The hand-unrolled source is a **different, larger program** than the one the compiler would have
produced. Its four bodies with explicit indices are harder to analyse than one body with a clean
induction variable, so the transformations the compiler would have applied — including its own
unrolling and vectorisation, which is what `-O3` turns up — have less to work with. The
optimisation was applied by hand, so it could not also be applied by the compiler, and the
compiler's version was better.

That is the general shape of the answer to this chapter's question. **The compiler will do the
local, mechanical transformations better than you will. What it will not do is change your
algorithm, your data layout, or your memory access pattern** — and those are the things
[ch22](#the-memory-hierarchy) showed dominate.

### The benchmark that measured nothing

There is a failure mode that makes every number in a benchmark meaningless, and it follows
directly from the compiler being good at this.

`tests/optimising_code/escapes.c` contains five functions doing identical arithmetic. They differ only in
what becomes of the result: dropped, returned, stored through a `volatile`, stored to a file-scope
variable nothing reads, or used in a condition that is never true.

Two of those loops are removed entirely and three survive, and which is which is not the division
most people expect. Problem 16.3 is that prediction, graded by compiling the file and counting —
so the answer comes from a compiler rather than from this chapter's opinion.

The rule underneath is simple to state and easy to get wrong in practice: a compiler may remove
work whose result **nothing can observe**. Returning it counts. Storing it through a `volatile`
counts, which is [ch03](#c-for-people-who-will-read-a-kernel)'s keyword doing the job it exists for. Storing it somewhere nothing
reads does not count, however much it looks like it should.

A benchmark whose work has been removed does not report zero. It reports a very small number, and
a spectacular speedup, and nothing about it looks wrong.

### What this cost

```{include} _generated/optimising-code-cost.md
```

Instruction counts say whether a source change survived the compiler. They do not say what the
surviving differences cost, and this chapter has been careful to claim only the first. The plain,
hoisted and reduced variants are the same program and therefore cost the same; whether the longer
unrolled version is also *slower* is a question about [ch24](#the-cpu)'s machinery, and the answer is
not automatic — more instructions can run in less time.

## What we measured

Instruction counts for five variants at three optimisation levels, on the reference architecture,
compiled and counted rather than run. CI regenerates them on every push, so the chapter's claims
about what this compiler does are checked against this compiler continuously — and if a future
version stops equalising those three, the build fails rather than the book quietly becoming wrong.

The timings are pending. They need the board and they are a different question.

## What this cannot tell you

**Whether fewer instructions is faster.** It very often is not, and [ch24](#the-cpu) is the chapter
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
two variants and the same for three, and says nothing about the outcome. `-O3` trades size for
speculation about what will help; whether the trade pays is a property of the program and the
machine together.

## Problems

Three. The first two are predictions about this book's own stamped result; the third is graded by
compiling.

**16.1 — Which variants does the compiler equalise?**
From the source alone, group the five by whether they come out the same at `-O2`. Graded against
`bench/results/loops-aarch64.json`, which CI regenerates — so a future compiler that changes its
mind changes the right answer rather than making the book wrong.

**16.2 — Which hand-optimisation backfired, and what does `-O3` do to it?**
Name the variant that costs more instructions than writing the loop plainly, and say whether
raising the level helps.

```bash
python3 -m pytest tests/optimising_code/test_problem_1_equalised.py
```

**16.3 — Which benchmark loops survive the compiler?**
Five functions, identical arithmetic, differing only in what becomes of the result. Two are
removed. Two of the five are traps and they are traps in opposite directions.

```bash
python3 -m pytest tests/optimising_code/test_problem_3_escapes.py
```

## Where to go next

Read the `-O2` and `-O3` sections of your compiler's own documentation — `gcc(1)` lists exactly
which passes each level enables, and it is a shorter and more useful document than its length
suggests. The two entries worth finding are the ones that name the transformations problems 16.1
and 16.2 are about.

[ch24](#the-cpu) is the chapter this one keeps deferring to. Instruction counts cannot say whether
the longer program is the slower one, because a modern core does not execute instructions one at a
time, and the next chapter is about what it does instead.
