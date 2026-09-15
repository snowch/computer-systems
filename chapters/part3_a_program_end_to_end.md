---
title: "Part III — What a computer does with a program"
short_title: "Part III"
---

(part3)=
# Part III · What a computer does with a program

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch09](#what-a-computer-does-with-a-program)–[ch12](#linking-and-loading) |
| **Target** | `xv6`, with [ch09](#what-a-computer-does-with-a-program) crossing to `host` and saying which figure came from where |
| **Assumes** | [Part I](#part1) |
:::

## What this part is for

One program, followed the whole way: from the text you typed to instructions a processor is
executing, with nothing in between left as magic.

[Part II](#part2) put your code at the address the machine starts from, which is the only situation
in which a program simply *is* somewhere. Every other program gets there by a route, and the route
turns out to be four separate programs, several file formats and a system call. This part walks it.
On the way it has to answer what a number in memory actually is, because a program is data before
it is instructions, and because the bugs that survive longest come from a value meaning something
other than what its name suggests.

It sits before [Part IV](#part4) for a reason that is nearly a pun: a kernel is a program. You
cannot usefully read one until you know what a program is, what a compiler leaves unfinished, and
who finishes it. [ch12](#linking-and-loading) ends at `exec`, which is precisely where Part IV begins.

## What it leaves out

How a compiler works. Parsing, intermediate representations, register allocation as a subject in
its own right — none of it is here. This part asks only what the compiler *produced* and whether
you can account for it. Why it chose one thing over another, and whether a better choice existed,
is [ch23](#optimising-code), and it is in [Part V](#part5) because the answer is about cost.

Also left out: every object format and loader other than the one in front of you. What generalises
is that a linker joins fragments, that some of a program's bytes are not stored because they are
known to be zero, and that something has to place the result in memory before it can run. The
spelling is local; the structure is not.

## Where to start

[ch09](#what-a-computer-does-with-a-program), in order. This part is a single argument in four steps and each chapter finishes a
question the one before it left open — a compiler that emits an unfinished object file, an object
file whose unfinished parts a linker fills, a linked file that is still only a file.

If you already know ELF and want the rest, [ch10](#representing-information) stands alone reasonably well; it is about
representation rather than tooling, and it is the chapter most likely to change what you think you
know.

## Which machine, and what it cannot tell you

Mostly `xv6`: compiled with the RISC-V cross-compiler, run under QEMU, disassembled and read.
[ch09](#what-a-computer-does-with-a-program) compiles the same source on both targets, because the claim it makes — that the
stages are a property of the toolchain and not of the machine — is only demonstrated by showing it
twice.

**Nothing in this part is timed.** Every figure here is structural: what a file contains, which
instructions the compiler emitted, what a program printed. That is not a limitation of the chapters
so much as the whole design — a stage boundary is a fact about the toolchain and survives being
observed under emulation, whereas a duration does not survive it at all.

## Where this leaves you

Able to take a program you did not write, find out what it is made of, and read the part of it the
processor actually sees.
