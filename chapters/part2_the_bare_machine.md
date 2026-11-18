---
title: "Part II · The machine with nothing on it"
short_title: "Introduction"
---

(part2)=
# Part II · The machine with nothing on it

:::{note} Part prerequisites and target
:class: chapter-header

| | |
|---|---|
| **Chapters** | [ch06](#a-trap-with-nothing-else)–[ch11](#fork-built-rather-than-read) |
| **Target** | `bare` — a RISC-V machine in QEMU without an operating system |
| **Assumes** | [Part I](#part1) |
:::

## What this part is for

Observe a RISC-V machine directly before reading the operating system that uses it. A trap
transfers execution to a handler. The early examples let you see the processor registers
involved. Later examples build software structures such as a descriptor table on top of those
mechanisms.

## What it leaves out

The machine has a serial console and just enough software to demonstrate each mechanism. A
file system, blocking pipes and a scheduler that resumes waiting processes need more
structure. [Part IV](#part4) shows that structure in xv6. Follow the build and assembly
recipes here. [Part III](#part3) explains how they work.

## Where to start

Open [ch06](#a-trap-with-nothing-else) and run the original trap program from your checkout.
Inspect where the trap landed and whether execution resumed. Follow the chapters in order so
each addition begins with a mechanism you have already seen.

## Which machine, and what it cannot tell you

The `bare` target boots the programs in QEMU without firmware or an operating system. Its
results describe the configured emulated machine. These examples are never timed, and a
physical board can have a different reset and firmware sequence.

## Where this leaves you

You can distinguish what the processor provides from what a kernel must implement.
