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
| **Chapters** | [ch23](#measuring)–[ch30](#vectors) |
| **Target** | `host` — Linux on real hardware, natively ([hardware](#prerequisites-and-setup)) |
| **Assumes** | [Part IV](#part4), and a machine of your own that meets [ch00](#prerequisites-and-setup)'s requirements |
:::

## What this part is for

[Part IV](#part4)'s chapters, asked again as questions about time.

This is not a second book about performance bolted to the first. Nearly every chapter here has a
counterpart earlier in the book and names it in its header: you arrive already knowing what a
context switch moves, what a page fault does, what a lock is for, and the only thing left to
establish is the price. That is a much better position to measure from than the usual one, because
the commonest way to be wrong about performance is not arithmetic — it is attributing a cost to a
mechanism you had only a rough idea about.

[ch23](#measuring) comes first and is the method: how to get a number you would defend, and how you
would know it was wrong. Everything after it is that method applied to one layer at a time, ending
with the two chapters that are about finding a cost in something you did not write.

It is last because it is the only part that needs the other four to have happened.

## What it leaves out

The whole of what *Systems Performance* @gregg-sysperf covers, deliberately, because that book is
where this one is trying to deliver you. Tracing and BPF, flame graphs, the network and storage
stacks, containers, observability across a fleet: none of it is here. What is here is the layer
underneath — the substrate whose quantities all of those tools report. The relationship is one-way,
and the reason to do this first is that a flame graph of a workload whose costs you cannot account
for is a picture rather than an answer.

It also leaves out a list of numbers to memorise. The figures are this board's. Some of them would
be different on yours by a factor that matters, and every chapter says so. What transfers is the
method, the shape of the answer, and knowing which questions the instrument cannot answer.

## Where to start

[ch23](#measuring), and this is the one instruction in the book worth being rigid about. Every chapter
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
[Appendix F](#appendix-f) is the translation between the two. The reason for the change is the
subject of this part rather than an accident of it: these chapters need performance counters that
both *count* and *sample*, and no purchasable RISC-V core does both. Staying on one architecture
would have cost two chapters their measurements, which is a worse trade than asking you to read a
second instruction set in three of them.

And where a thing genuinely cannot be measured on the available hardware — an absent unit, a
counter the firmware does not expose, a second machine that does not exist — the chapter says so,
shows the reasoning it used instead, and states what it would take to measure. It does not borrow a
number from somewhere else.

## Where this leaves you

Able to take a machine you have never seen, a program you did not write, and a claim about why it
is slow, and find out whether the claim is true.
