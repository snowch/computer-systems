---
title: "Part III · What a computer does with a program"
short_title: "Introduction"
---

(part3)=
# Part III · What a computer does with a program

:::{note} Part prerequisites and target
:class: chapter-header

| | |
|---|---|
| **Chapters** | [ch12](#what-a-computer-does-with-a-program)–[ch15](#linking-and-loading) |
| **Target** | `xv6`, with [ch12](#what-a-computer-does-with-a-program) crossing to `host` and saying which figure came from where |
| **Assumes** | [Part I](#part1) |
:::

## What this part is for

Follow a C program from source through compiler and linker output to the operating system
loading it. The tour shows how a value or instruction appears in each artefact so you can
track a change through the toolchain.

## What it leaves out

This part reads the files the compiler produces. [ch26](#optimising-code) examines
optimisation choices and their measured costs. The loading examples use the ELF format used by
these builds.

## Where to start

Open [ch12](#what-a-computer-does-with-a-program) and follow the generated files in order. If
you already know ELF and want practice with how C represents values, go to
[ch13](#representing-information).

## Which machine, and what it cannot tell you

The examples mainly use the RISC-V toolchain and xv6 under QEMU. The first chapter also shows
what the AArch64 toolchain produces from the same source. Nothing in this part is timed.

## Where this leaves you

You can identify which tool produced a file, what is still unresolved in it, and what the
operating system uses to load the program.
