---
title: "Systems From Scratch"
short_title: Preface
---

# Systems From Scratch

*From bits to cycles, measured on RISC-V.*

:::{warning} This book is being written
Chapter 0 is complete and the toolchain around it works end to end. Every other chapter is a
stub carrying its target, its question and the measurements it owes you. The
[project plan](https://github.com/snowch/computer-systems/blob/main/PLAN.md) has the outline and
what each chapter has to produce before it loses its `[DRAFT]` marker.
:::

## The question this book keeps asking

**Where do the cycles go, and how would I know?**

That second clause is the whole book. It is easy to learn that a cache miss is expensive, that a
system call costs more than a function call, that branch prediction exists. It is much harder to
be able to *find out* — on a machine in front of you, for a program you did not write — where the
time actually went, and to know when the answer you got is wrong.

So every layer here gets the same treatment: how it works, then what it costs, then how that cost
was measured and what the measurement could not see.

## Two machines, on purpose

Almost every book on this subject picks one target and lives with its limitations. This one uses
two, because the two halves of the question need different things.

```{figure} chapters/_figures/ch00-targets.svg
:alt: The xv6 and host targets side by side, with what each can and cannot answer.
:width: 100%

The division of labour. Every chapter declares which target it uses, and every figure records
which one produced it.
```

The first is **xv6**, the MIT teaching kernel, running under QEMU. It is a complete operating
system small enough to read in an afternoon, and you can stop the whole machine mid-trap and look
at anything. Parts I and II live there.

The second is a **StarFive VisionFive 2 Lite** — a RISC-V board with four in-order cores, sitting
on a desk, reached over SSH. Every number in Part III is measured on it, natively. Not in an
emulator, not on the laptop, not extrapolated from a different architecture.

The split is not a compromise; it is the argument. QEMU will happily answer a question about
nanoseconds and the answer will be meaningless, because it models no cache, no branch predictor
and no pipeline. Watching a program in a debugger tells you what it *does*. Only the board tells
you what it *costs*. Chapter 13 puts the same program through both and makes the gap concrete.

## How the numbers work

Every figure in this book comes from a JSON file under `bench/results/` that records the target,
the board or QEMU version, the kernel, the compiler, its flags, and a hash of the code that
produced the number. Nothing is typed into the prose by hand, and CI fails if a quoted figure's
hash stops matching the code in the repository.

Two consequences worth stating plainly. Where a measurement has not been taken yet, you will see
a box saying so rather than a plausible-looking placeholder. And where the hardware cannot answer
a question at all — this core has no vector unit, so chapter 21 cannot measure vectorisation — the
chapter says that, shows the reasoning it used instead, and does not quietly substitute a number
from somewhere else.

## Who it is for

Someone who has seen digital logic and a pipeline diagram, has spent years around computers, is
fluent in a scripting language, and has never had a reason to read a kernel. You do not need to
know C well; chapter 3 covers the parts that are really about addresses. You do not need OS
internals; that is Part II.

## What you will need

A laptop for Parts I and II, and a RISC-V board for Part III. Chapter 0 is the shopping list, the
installation, and a script that tells you which targets your machine can currently run.

## Problems

Every chapter ends with problems, and every problem is a stub under `tests/` with a test that
passes only when you have solved it. There is no answer key at the back — which means there is no
answer key to be wrong.
