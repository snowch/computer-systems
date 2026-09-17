---
title: "Reading a Listing"
short_title: "02 · Reading a Listing"
---

(reading-a-listing)=
# 02 · Reading a Listing

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` and `host` — the same function compiled for each, and nothing executed |
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **What it measures** | What the compiler made of one small function on each architecture: `bench/results/shapes-riscv64.json`, `bench/results/shapes-aarch64.json` |
:::

## The question

What is the compiler telling me, and what is it not?

Almost every chapter from here on puts a listing in front of you — the instructions a compiler
produced from source you can read beside it. Three of them are in the next chapter. You are never
asked to write assembly, and you are never asked to know every mnemonic; you are asked to say what
the compiler did, which is a much smaller skill and takes one chapter to acquire.

Acquire it now rather than in passing, because the notation that carries most of the
weight — parentheses, which mean memory — is also the most likely to be read as something else.

## The material

### One function, two instruction sets

Here is a function with no cleverness in it at all:

```{literalinclude} ../sysfs/lib/shapes.c
:language: c
:start-at: /* Two conditionals and three exits
:end-before: /* A loop with a carried dependency
```

Compiled for each of the book's two architectures, at the same optimisation level — how hard the
compiler was asked to try — by the same version of the same compiler. The conditions line under
each listing says exactly which:

```{include} _generated/reading-a-listing-clamp.md
```

The rest of this chapter is how to read those two.

### How a listing is laid out

**The left-hand column is an address**, in hexadecimal, counted from the start of the function.
`0:` is the first instruction, and the number on the next line tells you how many bytes it took —
so a second instruction at `4:` means the first was four bytes long. In the RISC-V listing you will
also find instructions two bytes apart, because RISC-V has short forms of its commonest
instructions @riscv-isa-unprivileged and the compiler uses them unasked. Instructions here are
*not* all the same length, and [ch06](#a-trap-with-nothing-else) turns on that fact.

**Then the mnemonic**: `blt` is branch-if-less-than, `mv` is move, `ret` is return. You are not
expected to know these, and this book never asks you to write assembly — only to read enough of it
to say what the compiler did.

**Then the operands, destination first.** `mv a1,a0` copies `a0` into `a1`, not the other way
round. That order is the assembler's convention @riscv-isa-unprivileged and it is the one thing
most likely to mislead you if you skim.

**`a0`, `a1`, `a2` are registers** — the processor's own named slots, the fastest storage a program
has. The `a` ones carry arguments and return values @riscv-psabi, which is why a function's first
argument arrives in `a0` and its answer leaves in `a0`. [Appendix A](#appendix-a) lists them all.

**Parentheses mean memory, and the number in front is a byte offset.** `4(a0)` is *the memory at
the address in `a0`, plus four bytes* — not `a0` times anything. Nearly every listing in
[Part I](#part1) turns on that one piece of notation, and the offset is usually the width of
whatever is stored at that address, which is how the same C source becomes `4(a0)` in one function
and `8(a0)` in another.

**Everything under a listing is provenance**: which compiler, which flags, which result file it was
captured from. It is there so that a listing you find surprising can be regenerated rather than
argued about.

### What the two disagree about

Read the second comparison in each. AArch64 settles it with `csel` — compute both candidates,
select one, never branch. RV64GC — the particular set of RISC-V instructions that xv6 and every
RISC-V example here are built for — has no conditional select @riscv-isa-unprivileged, so the same
decision has to be a branch, and the function comes out with three separate exits.

That is a real difference, and it is not a difference in speed. Nothing above says which is
faster, and *What this cannot tell you* below says why not.

Two smaller things are visible in the same listings. The RISC-V one has labels — `.L4`, `.L6` —
sitting inside the function, and the AArch64 one has none; that is a division of labour between
two tools you meet in [ch12](#what-a-computer-does-with-a-program) and
[ch15](#linking-and-loading), and for now it is enough to have noticed it. And `sext.w`, which
RISC-V emits on each path and AArch64 does not emit anywhere: RISC-V keeps a 32-bit `int` in a
64-bit register and has to say so, while AArch64 has a 32-bit view of the register and uses it.
Neither is in the C. Both are the kind of thing [ch14](#machine-level-code-on-riscv) is for.

:::{note} None of that was typed
`bench/run_disasm.py` compiled `sysfs/lib/shapes.c` for each architecture, ran `objdump` on the
object file, and wrote a stamped result. The block above is rendered from those results, and CI
regenerates both on every push and fails if one instruction differs.

It can do that because a listing depends on the compiler and not on the machine — so unlike every
number in [Part V](#part5), this one is checked automatically, every time.
:::

## What we measured

One function, compiled for each of the book's instruction sets by the same compiler at the same
optimisation level. Nothing was executed and nothing was timed: a listing is a fact about a
compiler, so it is the one kind of result in this book that CI can regenerate and check on every
push. [ch24](#measuring) is about the kind that cannot be.

## What this cannot tell you

**Which of the two is faster.** This is the mistake the chapter exists to prevent, and it is
tempting precisely because the listings are short enough to count. AArch64 settles the second
comparison without branching and RISC-V cannot, so one comes out shorter — and that tells you
nothing about time. A branch the processor guessed right is nearly free and one it guessed wrong
is not; `csel` pays a fixed price either way, and has to wait for both candidates before it can
choose. Which wins depends on the data the function is given, and the only way to find out is to
run both on hardware that can be asked. [ch26](#optimising-code) and [ch27](#the-cpu) do that.

**What any of these instructions costs.** A mnemonic is a name, not a price. Nothing in a listing
says how many cycles an instruction takes, whether its operands were in cache, or whether the core
ran it at the same time as its neighbour. Those are properties of a machine and this page has not
been near one.

**Whether the compiler was right.** It made these choices at one optimisation level, for one
target, from one version of one compiler — all of which the conditions line records, because all
of them change the answer. A different flag produces a different listing from identical source,
which is [ch26](#optimising-code)'s subject.

**Anything about a program.** One function with no calls in it is the easiest possible listing.
Real code spends its instructions on stack frames, calling conventions and address arithmetic, and
none of that is visible here. [ch14](#machine-level-code-on-riscv) is where a listing stops being
a curiosity and starts being a thing you read to answer a question.

## Problems

Three, in `tests/reading_a_listing/`. Each is a Python stub: this chapter comes before any C.

**2.1 — How long is each instruction?**
Given the address column of a listing, say how many bytes each instruction occupied. RISC-V has
short forms of its commonest instructions and the compiler uses them unasked, so the answer is not
the same number every time.

```bash
python3 -m pytest tests/reading_a_listing/test_problem_1_lengths.py
```

**2.2 — Does this operand touch memory?**
Eleven operands drawn from both instruction sets. Say which of them name a register or a literal,
and which reach memory. One pair differs only by punctuation and disagrees.

```bash
python3 -m pytest tests/reading_a_listing/test_problem_2_memory.py
```

**2.3 — How wide was the element?**
Given a load and its offset, say how many bytes wide the thing being stepped over was. This is the
same fact the next chapter opens on, approached from the instruction rather than from the C.

```bash
python3 -m pytest tests/reading_a_listing/test_problem_3_width.py
```

## Where to go next

[Appendix A](#appendix-a) is the RISC-V register and CSR reference, and
[Appendix F](#appendix-f) is this page's counterpart for AArch64 — three differences that change
how a listing reads. The assembler syntax and the register roles are defined in the RISC-V
unprivileged specification @riscv-isa-unprivileged and the psABI @riscv-psabi.

[ch03](#memory-is-one-array) is next: one complete program, and its listing read the way this
chapter has just shown you.
