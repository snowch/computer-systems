---
title: "Reading a Listing"
short_title: "01 · Reading a Listing"
---

(reading-a-listing)=
# 01 · Reading a Listing

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` and `host` — the same function compiled for each, and nothing executed |
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **What it measures** | What the compiler made of one small function on each architecture: `bench/results/shapes-riscv64.json`, `bench/results/shapes-aarch64.json` |
:::

## The question

**What is the compiler telling me, and what is it not?**

Almost every chapter from here on puts a listing in front of you — the instructions a compiler
produced from source you can read beside it. Two of them are in the next chapter. You are never
asked to write assembly, and you are never asked to know every mnemonic; you are asked to say what
the compiler did, which is a much smaller skill and takes one chapter to acquire.

It is worth acquiring now rather than in passing, because the one piece of notation that carries
most of the weight is also the one most likely to be read as something else.

## The material

### How a listing is laid out

**The left-hand column is an address**, in hexadecimal, counted from the start of the function.
`0:` is the first instruction, and the number on the next line tells you how many bytes it took —
so a second instruction at `4:` means the first was four bytes long. You will also find
instructions two bytes apart, because this architecture has short forms of its commonest
instructions @riscv-isa-unprivileged and the compiler uses them unasked. Instructions here are
*not* all the same length, and [ch05](#a-trap-with-nothing-else) turns on that fact.

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
whatever the pointer points at, which is how the same C source becomes `4(a0)` in one function and
`8(a0)` in another.

**Everything under a listing is provenance**: which compiler, which flags, which result file it was
captured from. It is there so that a listing you find surprising can be regenerated rather than
argued about.

### The same function in two instruction sets

Here is a function with no cleverness in it at all:

```{literalinclude} ../sysfs/lib/shapes.c
:language: c
:start-at: /* Two conditionals and three exits
:end-before: /* A loop with a carried dependency
```

Compiled for each of the book's two architectures, at the same optimisation level, by the same
version of the same compiler — the conditions line under each listing says exactly which:

```{include} _generated/reading-a-listing-clamp.md
```

Read the second comparison in each. AArch64 settles it with `csel` — compute both candidates,
select one, never branch. RV64GC cannot: there is no conditional select in `rv64gc`
@riscv-isa-unprivileged, which is what xv6 and every RISC-V example here are built for, so the same
decision has to be a branch and the function comes out with three separate exits.

That is a real difference and you should resist the obvious conclusion about it. Nothing above
says which is faster. A predicted branch is nearly free and an unpredictable one is not; `csel`
pays a fixed price either way and creates a dependency the branch does not have. Which wins
depends on the data, and finding out takes a machine — [ch25](#optimising-code) and [ch26](#the-cpu) are where
that happens. Here it is enough to have seen that the choice exists.

Two smaller things in the same listings, both worth checking yourself:

```bash
make bench-listings                                   # leaves both object files in sysfs/build/
riscv64-linux-gnu-readelf -rW sysfs/build/shapes-riscv64.o
aarch64-linux-gnu-readelf -rW sysfs/build/shapes-aarch64.o
```

The RISC-V listing has `.L4` and `.L6` sitting *inside* the function, and the first command says
why: there is a relocation for every branch in it, naming those labels. The assembler did not
settle its own branch distances, because the linker is still allowed to shorten instructions —
RISC-V calls that relaxation @riscv-psabi — and a distance settled before that would be wrong
afterwards. The AArch64 object has no relocations in its text at all; its assembler knew the
answers and the labels were discarded. The same job, divided differently between the assembler and
the linker.

The second thing is `sext.w`, which RISC-V emits on each path and AArch64 does not emit anywhere:
one keeps a 32-bit `int` in a 64-bit register and has to say so, the other has a 32-bit view of the
register and uses it. Neither is in the C. Both are the kind of thing [ch13](#machine-level-code-on-riscv) is for.

:::{note} None of that was typed
`bench/run_disasm.py` compiled `sysfs/lib/shapes.c` for each architecture, ran `objdump` on the
object file, and wrote a stamped result. The block above is rendered from those results, and CI
regenerates both on every push and fails if one instruction differs.

It can do that because a listing depends on the compiler and not on the machine — so unlike every
number in [Part V](#part5), this one is checked automatically, every time. Both halves of that sentence
matter, and [ch23](#measuring) is about the half that cannot be.
:::

## What we measured

One function, compiled for each of the book's instruction sets by the same compiler at the same
optimisation level. Nothing was executed and nothing was timed: a listing is a fact about a
compiler, so it is the one kind of result in this book that CI can regenerate and check on every
push. [ch23](#measuring) is about the kind that cannot be.

## What this cannot tell you

**Which of the two is faster.** This is the mistake the chapter exists to prevent, and it is
tempting precisely because the listings are short enough to count. AArch64 settles the second
comparison without branching and RISC-V cannot, so one is three instructions shorter — and that
tells you nothing about time. A predicted branch is nearly free; an unpredictable one costs tens
of cycles; `csel` pays a small fixed price and creates a dependency the branch does not have.
Which wins depends on the data the function is given, and the only way to find out is to run both
on hardware that can be asked. [ch25](#optimising-code) and [ch26](#the-cpu) do that.

**What any of these instructions costs.** A mnemonic is a name, not a price. Nothing in a listing
says how many cycles an instruction takes, whether its operands were in cache, or whether the core
ran it at the same time as its neighbour. Those are properties of a machine and this page has not
been near one.

**Whether the compiler was right.** It made these choices at one optimisation level, for one
target, from one version of one compiler — all of which the conditions line records, because all
of them change the answer. A different flag produces a different listing from identical source,
which is [ch25](#optimising-code)'s subject.

**Anything about a program.** One function with no calls in it is the easiest possible listing.
Real code spends its instructions on stack frames, calling conventions and address arithmetic, and
none of that is visible here. [ch13](#machine-level-code-on-riscv) is where a listing stops being
a curiosity and starts being a thing you read to answer a question.

## Problems

Three, in `tests/reading_a_listing/`. Each is a Python stub: this chapter comes before any C.

**1.1 — How long is each instruction?**
Given the address column of a listing, say how many bytes each instruction occupied. RISC-V has
short forms of its commonest instructions and the compiler uses them unasked, so the answer is not
the same number every time.

```bash
python3 -m pytest tests/reading_a_listing/test_problem_1_lengths.py
```

**1.2 — Does this operand touch memory?**
Eleven operands drawn from both instruction sets. Say which name a register and which reach
memory. Two of them differ by one character and disagree.

```bash
python3 -m pytest tests/reading_a_listing/test_problem_2_memory.py
```

**1.3 — How wide was the element?**
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
