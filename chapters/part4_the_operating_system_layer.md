---
title: "Part IV — The operating system layer"
short_title: "Part IV"
---

(part4)=
# Part IV · The operating system layer

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch14](#traps-and-system-calls)–[ch21](#the-same-program-on-both-targets) |
| **Target** | `xv6` — the teaching kernel under QEMU, with [ch21](#the-same-program-on-both-targets) crossing to `host` |
| **Assumes** | [Part II](#part2), [Part III](#part3) |
:::

## What this part is for

A complete operating system, small enough to read, taken apart one mechanism at a time.

[Part II](#part2) removed the entanglement deliberately: each primitive on its own, on a machine
with nothing else running. This part puts it back, and the entanglement turns out to be most of
what an operating system *is*. A trap handler that also has to find the right process, on the right
hart, without losing an interrupt, while another hart is in the same code, is not a harder version
of [ch04](#a-trap-with-nothing-else)'s handler. It is a different subject, and it is this one.

The kernel is xv6, because it is short enough to read in full and you can stop the entire machine
in the middle of a trap and look at anything. That matters more than modernity here. A production
kernel would have the same mechanisms buried under thirty years of necessary special cases, and you
would be taking someone's word for which lines were the point.

The order is the argument. Traps come before virtual memory because a page fault is a trap.
Interrupts come before locks because a lock's first job is to survive one. Locks come before
scheduling because a scheduler is largely the thing that needed them.

## What it leaves out

Cost. Every question of the form *how long does this take* is refused here and asked again in
[Part V](#part5), where there is hardware that can answer it. This is not tidiness — a timing taken
under emulation is a fact about the emulator, and a chapter that produced one would be quietly
teaching you to trust the wrong instrument.

Linux, except by contrast. xv6 is a teaching kernel and some of its choices are simplifications
rather than designs; the chapters say which, and [ch27](#the-os-layers-cost) puts the same operations to a
production kernel. Left out entirely: networking, a scheduler with a policy worth arguing about,
and the parts of a file system that exist because disks are large rather than because crashes
happen.

## Where to start

[ch14](#traps-and-system-calls), in order. Each chapter names the one before it as its prerequisite and means it.

[ch21](#the-same-program-on-both-targets) is the exception and can be read early if you want to know where the book is going.
It runs one program on both targets and is the hinge into [Part V](#part5) — the chapter that
stops being about how a thing works and starts being about how you would find out what it costs.

## Which machine, and what it cannot tell you

`xv6` under `qemu-system-riscv64`, read in a debugger.

**Nothing in this part is timed, and nothing in it may be.** QEMU is the right instrument for
structure and the wrong one for everything else. It will tell you
exactly which register held the faulting address and in what order the stores happened in the
program's own view; it models no cache, no branch predictor, no store buffer and no memory latency,
so it cannot tell you what any of it cost or what a second hart really does to the first.

The sharper limit is that **it is a poor liar rather than an obvious one.** A duration measured
here is a real number, reproducible, and about the host machine and the translation strategy rather
than about RISC-V — and once written into a table it is indistinguishable from a measurement. That
is why the rule is absolute and why a check enforces it rather than a convention.

## Where this leaves you

Knowing what the mechanisms are and where they live, and therefore able to ask the only question
left, which is what they cost.
