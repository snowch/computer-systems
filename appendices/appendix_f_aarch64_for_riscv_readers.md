---
title: "Appendix F — AArch64 for RISC-V Readers"
short_title: "Appendix F"
---

(appendix-f)=
# Appendix F · AArch64 for RISC-V Readers

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

This is a translation rather than a reference. It is written for someone who has read
[ch14](#machine-level-code-on-riscv) and is about to read [ch26](#optimising-code), and it is organised as *you know this already,
here it is again*. For anything not in the book's path, the architecture reference manual
@arm-arm is the document; this page will not substitute for it and does not try.

## Why there are two

[Part III](#part3) and [Part IV](#part4) are RISC-V because the kernel small enough to read in an afternoon is a RISC-V
kernel. [Part V](#part5) is AArch64 because that is where the performance counters work: sampling needs a
PMU that can raise an interrupt on counter overflow, and no affordable RISC-V core does both.
[Appendix H](#appendix-h) has the evidence and [ch28](#memory-ordering-on-real-hardware) has the return — a reader shown one weak memory
model concludes that model *is* memory ordering.

So the crossing is deliberate, and this page is the cost of it, paid in one place.

## Registers

Thirty-one general-purpose registers plus a zero register and a stack pointer, which is nearly the
same count as RISC-V and arrived at differently.

| | RISC-V | AArch64 |
|---|---|---|
| General purpose | `x0`–`x31`, `x0` hardwired zero | `x0`–`x30`, plus `xzr`/`wzr` |
| 32-bit form | none — use `w`-suffixed instructions | `w0`–`w30`, the low half of `x0`–`x30` |
| Zero | `x0`, a register | `xzr`, an operand encoding |
| Stack pointer | `sp` = `x2`, an ordinary register | `sp`, separate and not `x31` |
| Return address | `ra` = `x1`, by convention | `x30`/`lr`, written by the branch instruction |
| Arguments | `a0`–`a7` | `x0`–`x7` |
| Return value | `a0`, `a1` | `x0`, `x1` |
| Callee-saved | `s0`–`s11` | `x19`–`x28` |
| Frame pointer | `s0`/`fp`, by convention | `x29`/`fp`, by convention |

Two differences that change how listings read.

**The `w` registers are not a convention, they are the instruction.** `add w0, w1, w2` is a
32-bit add that zero-extends into the full register; `add x0, x1, x2` is a 64-bit add. RISC-V
spells this with separate mnemonics (`addw` against `add`). You will see `w` registers constantly
in [ch26](#optimising-code)'s listings wherever an `int` is involved, and the zero-extension is free rather
than an extra instruction.

**`x31` is two registers depending on the instruction.** In most positions the encoding means
`xzr`; in a few it means `sp`. This is why the zero register is described here as an operand
encoding rather than a register — it does not exist as a thing you can point at.

## Loads and stores

| | RISC-V | AArch64 |
|---|---|---|
| Load a word | `lw a0, 8(a1)` | `ldr w0, [x1, #8]` |
| Load a doubleword | `ld a0, 8(a1)` | `ldr x0, [x1, #8]` |
| Store | `sd a0, 8(a1)` | `str x0, [x1, #8]` |
| Indexed | compute the address first | `ldr w0, [x1, x2, lsl #2]` |
| Pair | — | `stp x29, x30, [sp, #-16]!` |
| Post-increment | — | `ldr q1, [x2], #16` |

Three things to know before reading any AArch64 listing.

**The addressing modes do arithmetic.** `[x1, x2, lsl #2]` scales an index by four and adds it, in
the load. RISC-V would need a shift and an add first. This is why an AArch64 inner loop over an
array is often two instructions shorter than the RISC-V one for the same C, and it is visible in
every listing in [ch26](#optimising-code).

**`stp` and `ldp` move two registers at once.** Almost every non-leaf function prologue you will
see is `stp x29, x30, [sp, #-16]!` — save the frame pointer and the return address, and decrement
the stack pointer, in one instruction. The `!` is the write-back. [ch14](#machine-level-code-on-riscv)'s RISC-V prologues
take three instructions to do the same thing.

**The suffix after the bracket is where the increment went.** `[x2], #16` adds sixteen to `x2`
*after* the access; `[x2, #16]!` adds it before. Neither exists in RISC-V, and both appear in
vectorised loops in [ch31](#vectors).

## Branches and conditions

This is the largest difference and the one that changes how you read a loop.

RISC-V compares and branches in one instruction: `blt a0, a1, label`. AArch64 sets flags and then
branches on them:

```
cmp  x0, x1
b.lt label
```

The flags are a side effect that persists, which buys two things RISC-V has no equivalent of.

**Conditional select.** `csel x0, x1, x2, lt` writes one of two registers depending on the flags,
with no branch at all. [ch27](#the-cpu) is about what that is worth: a branch the predictor cannot
learn costs a pipeline flush every time, and a `csel` costs one instruction always.

**Compare-and-branch-on-zero.** `cbz`/`cbnz` are the exception that does not use the flags, and
they are extremely common because testing against zero is extremely common.

| | RISC-V | AArch64 |
|---|---|---|
| Compare and branch | `blt a0, a1, L` | `cmp x0, x1` then `b.lt L` |
| Branch if zero | `beqz a0, L` | `cbz x0, L` |
| Select without branching | — | `csel x0, x1, x2, cond` |
| Call | `jal ra, f` | `bl f` |
| Tail call | `j f` | `b f` |
| Return | `ret` (`jalr x0, 0(ra)`) | `ret` (uses `x30`) |

## Atomics and ordering

[ch20](#locks-and-memory-ordering) prints both of these from real disassembly and [ch28](#memory-ordering-on-real-hardware) is the chapter about
what the difference means.

| | RISC-V | AArch64 |
|---|---|---|
| Atomic read-modify-write | `amoswap.w.aq`, `amoadd.d`, … | `ldadd`, `swp`, … (LSE), or `ldxr`/`stxr` |
| Acquire | `fence r,rw` after the load | `ldar` — the load itself |
| Release | `fence rw,w` before the store | `stlr` — the store itself |
| Full barrier | `fence rw,rw` | `dmb ish` |

**The asymmetry is the thing to carry away.** RISC-V puts an instruction *between* the two
operations being ordered; AArch64 folds the ordering into one of them. A reader who learned that a
barrier is something you put between two things will not recognise `stlr` as a barrier at all,
which is exactly why [ch28](#memory-ordering-on-real-hardware) puts them side by side rather than teaching one.

Both spell the same requirement. Neither spelling is the concept.

## Vectors

NEON, in one paragraph, because [ch31](#vectors) is the chapter.

Thirty-two registers, `v0`–`v31`, 128 bits each, addressed by an *arrangement specifier* that says
how to divide them: `v0.4s` is four 32-bit lanes, `v0.2d` is two 64-bit ones, `v0.16b` is sixteen
bytes. The same registers are named `q0`–`q31` when the whole 128 bits are meant, and `s0`/`d0`
when a single scalar float or double is meant.

That last point is a trap [ch31](#vectors) fell into and records: an instruction naming a `v`
register is not evidence of vectorisation. This compiler builds a floating-point zero with
`movi v0.2s, #0`, in a function whose loop it has refused to widen.

## What this cannot tell you

**How the two architectures differ where this book does not go.** Exceptions, privilege levels,
the MMU, system registers — all different, none of it here, because [Part V](#part5) does not read the
kernel and [Part IV](#part4) does not run on AArch64.

**Which is better.** They make different choices and the book uses both for what each is good for.
Nothing on this page is an argument.

**What any of it costs.** This is a translation table. Every number about cost in this book is
measured, and none of it is here.

## Where to go next

The ARM architecture reference manual for AArch64 @arm-arm is the document, and its A64
instruction index is the part to keep open. The procedure call standard for AArch64
@arm-aapcs64 is the equivalent of the RISC-V psABI @riscv-psabi and is what decides the register
roles above.
