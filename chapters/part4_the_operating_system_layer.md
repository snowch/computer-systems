---
title: "Part IV · The operating system layer"
short_title: "Introduction"
---

(part4)=
# Part IV · The operating system layer

:::{note} Part prerequisites and target
:class: chapter-header

| | |
|---|---|
| **Chapters** | [ch16](#traps-and-system-calls)–[ch23](#the-same-program-on-both-targets) |
| **Target** | `xv6` — the teaching kernel under QEMU, with [ch23](#the-same-program-on-both-targets) crossing to `host` |
| **Assumes** | [Part II](#part2), [Part III](#part3) |
:::

## What this part is for

Follow the mechanisms from [Part II](#part2) through the xv6 teaching kernel. See how the
kernel keeps track of the current process, routes a trap, chooses when a task can run and
arranges safe access to files.

## What it leaves out

The examples cover the xv6 mechanisms used in the exercises. Linux adds different policies and
implementation details. [ch29](#the-os-layers-cost) measures selected calls and faults on
native Linux.

## Where to start

Open [ch16](#traps-and-system-calls) and follow one call through the trap path. Read the
chapters in order so you can use that path when you reach page faults and context switches.

## Which machine, and what it cannot tell you

The xv6 examples run in QEMU. Use the debugger and recorded counts to follow execution.
Emulated runs are never timed for this book. [ch23](#the-same-program-on-both-targets) pairs a
native timing with a correctness comparison between targets.

## Where this leaves you

You can name the kernel mechanism involved in a program’s behaviour, trace where it acts and
choose a measurement question for [Part V](#part5).
