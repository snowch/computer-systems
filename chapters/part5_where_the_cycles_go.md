---
title: "Part V — Where the cycles go"
short_title: "Introduction"
---

(part5)=
# Part V · Where the cycles go

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch24](#measuring)–[ch31](#vectors) |
| **Target** | `host` — Linux on real hardware, natively ([ch01](#setting-up-the-board)) |
| **Assumes** | [Part IV](#part4), and a machine of your own that meets [Appendix H](#appendix-h)'s requirements |
:::

## What this part is for

[Part IV](#part4)'s chapters, asked again as questions about time.

Nearly every chapter here has a counterpart earlier in the book and names it in its header, so you
arrive already knowing what a context switch moves, what a page fault does and what a lock is for.
Only the price is left to establish. That is a better position to measure from than the usual one,
because the commonest way to be wrong about performance is not arithmetic — it is attributing a
cost to a mechanism you had only a rough idea about.

[ch24](#measuring) comes first and is the method: how to get a number you would defend, and how you
would know it was wrong. Everything after it is that method applied to one layer at a time — the
memory, the compiler, the core, the kernel — then to a whole machine at once, and last to the one
unit a program has to be rewritten to use.

It is last because it is the only part that needs the other four to have happened.

## What it leaves out

The whole of what *Systems Performance* @gregg-sysperf covers, deliberately, because that book is
where this one is trying to deliver you. Tracing and BPF, flame graphs, the network and storage
stacks, containers, observability across a fleet: none of it is here. This part is the layer
underneath — cache misses, faults and context switches are what all of those tools report, and
this is where they get their meaning. Do this first, because a flame graph of a workload whose
costs you cannot account for is a picture rather than an answer.

It also leaves out a list of numbers to memorise. The figures are this board's. Some of them would
be different on yours by a factor that matters, and every chapter says so. What transfers is the
method, the shape of the answer, and knowing which questions the instrument cannot answer.

## Where to start

[ch24](#measuring), and this is the one instruction in the book worth being rigid about. Every chapter
after it produces numbers using its method, and reading them without it is how people end up
confident and wrong — a measurement is not self-describing, and the difference between a defensible
figure and a plausible one is entirely in how it was taken.

After that the header rows will route you: each chapter names the earlier chapter whose cost it
answers, so you can follow a single mechanism from what it does to what it charges.

## Which machine, and what it cannot tell you

A small Linux machine on a desk, reached over SSH, running natively. Every number in this book that
is a *cost* was measured here, and each one records the board, the kernel, the compiler and a hash
of the code that produced it.

Several chapters go further than using the machine and depend on it — a particular cache hierarchy,
a particular core, a particular set of performance counters exposed by a particular firmware. Those
say so in an **Assumes** row of their own. On a different board the mechanism holds and the figures
will not match, and where that is likely the chapter says what to expect instead of pretending the
number is universal.

The disassembly here is AArch64, not the RISC-V you learned in [Part III](#part3).
[Appendix F](#appendix-f) is the translation between the two. The change of architecture is not an
accident: these chapters need performance counters that
both *count* and *sample*, and no purchasable RISC-V core does both. Staying on one architecture
would have cost two chapters their measurements, which is a worse trade than asking you to read a
second instruction set in five of them.

And where a thing genuinely cannot be measured on the available hardware — an absent unit, a
counter the firmware does not expose, a second machine that does not exist — the chapter says so,
shows the reasoning it used instead, and states what it would take to measure. It does not borrow a
number from somewhere else.

More than once this part sets out to reproduce a well-known effect and finds it mostly gone. Bias
from where the stack sits, the penalty for false sharing, the clean step that betrays a cache line:
each is real, each is in the literature, and on this newer core each came back smaller than the
folklore promises, sometimes to nothing. That is not the measurement failing. A modern core spends
its transistors hiding exactly these effects, so the older the demonstration the likelier the
silicon has closed it, and the number you inherited was taken on a machine that no longer exists.
It is said once here because you will meet it in three chapters, and the answer is the same each
time: measure yours.

## Where this leaves you

Able to take a machine you have never seen, a program you did not write, and a claim about why it
is slow, and find out whether the claim is true.
