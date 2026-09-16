---
title: "Getting started"
short_title: "Introduction"
---

(part0)=
# Getting started

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch00](#prerequisites-and-setup)–[ch01](#setting-up-the-board) |
| **Target** | all three, which is the point |
| **Assumes** | nothing |
:::

## What this part is for

Two machines to get working, and a script that says what each one can currently run.

The book uses three targets on two machines, and the two machines are not equally urgent. The
computer you are reading this on runs `bare` and `xv6` under QEMU, needs one cross compiler, and
covers everything up to [Part V](#part5). The board is a second machine, it is the only place a
timing may be measured, and nothing needs it until [ch24](#measuring).

So the two chapters are in that order, and they are separate on purpose: you can finish
[ch00](#prerequisites-and-setup) this afternoon on a laptop, and do
[ch01](#setting-up-the-board) whenever the hardware turns up. It is the next chapter, but
twenty-two chapters sit between finishing the first and *needing* the second.

## What it leaves out

**The decision about what to buy.** That is [Appendix H](#appendix-h), because it is read once,
before you own anything, and then only to settle an argument with a spec sheet. This part assumes
the machines exist.

**Any reason for the arrangement.** The preface argues for three targets on two machines and for
the instruction sets not matching. These chapters take that as settled and get it working.

## Where to start

[ch00](#prerequisites-and-setup), on whatever you are reading this on. It ends with a program
compiled for both architectures and run under both emulated targets, which is how you know the
setup is real rather than merely installed.

Then [ch01](#setting-up-the-board) when the board arrives — or later. Nothing before
[Part V](#part5) depends on it, and [ch00](#prerequisites-and-setup)'s script will tell you at any
point which targets your machines can currently run.

## Which machine, and what it cannot tell you

Both, which is what makes this a part rather than a chapter. The emulated targets answer questions
about what a program *does* and **nothing here or in Parts I to IV is ever timed** —
QEMU models no cache, no branch predictor and no memory latency, so a duration measured inside it
describes the laptop and the translation strategy rather than the machine being emulated. The
board answers questions about cost and is the only place in the book a timing may be taken.

What neither can tell you yet is whether any of it is *worth* measuring. Setting a machine up
proves it runs; it does not prove a number coming out of it means anything, and
[ch24](#measuring) is the chapter that takes that apart.

## Where this leaves you

Two machines that work, and a script that says so — which is a smaller claim than it sounds and
exactly the right one. You will not have learned anything about computers yet. You will have the
apparatus the rest of the book measures with, and a way to check at any point that it is still
telling the truth.
