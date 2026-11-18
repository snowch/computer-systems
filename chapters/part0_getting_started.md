---
title: "Getting started"
short_title: "Introduction"
---

(part0)=
# Getting started

:::{note} Part prerequisites and target
:class: chapter-header

| | |
|---|---|
| **Chapters** | [ch00](#prerequisites-and-setup)–[ch01](#setting-up-the-board) |
| **Target** | `bare` and `xv6` on your computer. `host` on native Linux for timings. |
| **Assumes** | You can program in another language. |
:::

## What this part is for

Check the programming tools on your computer first. You can use the QEMU emulator there to run
both `bare` and `xv6`. Set up a separate native Linux machine when you are ready to run timing
experiments.

## What it leaves out

[Appendix H](#appendix-h) explains the hardware requirements and how to check a machine you
already have.

## Where to start

Open [ch00](#prerequisites-and-setup). Clone the repository, run the setup check and boot xv6.
If you have suitable native Linux hardware, use [ch01](#setting-up-the-board) to check its
performance counters before starting [Part V](#part5).

## Which machine, and what it cannot tell you

The `bare` and `xv6` examples are never timed for the book. Use their output to see what code
does. Hardware timings come from the native `host` target.

## Where this leaves you

You can identify which examples your setup can run and tell a missing tool from a program that
built and produced an unexpected result.
