---
title: "Part II — The machine with nothing on it"
short_title: "Part II"
---

(part2)=
# Part II · The machine with nothing on it

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch04](#ch04)–[ch08](#ch08) |
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Assumes** | [Part I](#part1) |
:::

## What this part is for

Five chapters, each building one primitive of the machine with nothing else in the way.

The difficulty this part answers is real and it is the usual reason people stall on kernels. A
kernel presents its primitives already entangled. The first trap you meet in xv6 arrives with a
process table, a page table, a scheduler and a lock attached to it, and the code that handles it is
correct about all of them at once. You are asked to learn what a trap *is* from a page that assumes
you already know.

So: no kernel. No library, no loader, no operating system, nothing at the far end of a `printf`.
The machine comes out of reset and runs your instructions. Each chapter then adds exactly one
mechanism to a machine that has none — a trap, an interrupt, a page table, a system call, and
finally a second process created from the first.

It sits here, rather than inside [Part IV](#part4), because these primitives belong to the
*hardware*. A trap vector, a saved program counter and the instruction that returns from a trap are
in the privileged specification, not in anybody's kernel. Having written the three-instruction
version yourself and watched it work changes what xv6's trap handling looks like: an arrangement of
things you have built, rather than a wall of new ideas.

## What it leaves out

Everything that makes a kernel a kernel. No scheduling policy, no file system, no device beyond the
one serial port needed to see anything at all, no allocator beyond what a page table requires.

File descriptors are the case worth explaining, because anyone who knows `fork` from the outside
will expect them and they are not here. The reason is this part's own rule. A descriptor is not a
primitive of the machine — nothing in the privileged specification has heard of one. It is a
kernel's invention: an index into a table a kernel decided to keep. Building it alongside `fork`
would put two ideas into one chapter, which is precisely the thing this part exists to stop doing.

The insight descriptors are usually used to carry — that `fork` copies some of what a process has
and shares the rest — is available here without them, and more plainly. [ch08](#ch08)'s child gets
a copy of the address space and no copy whatsoever of the serial port, because the port is at a
physical address and there is only one of it. Descriptors, and the several kinds of open file that
make a table of them worth having at all, are [ch19](#ch19).

And one thing it leaves out on purpose, which is worth saying plainly: **you will use a linker
script and read assembly here, and neither is explained until [Part III](#part3).** Treat them as
recipes. [ch11](#ch11) covers the instructions and [ch12](#ch12) covers the script. This part needs
them working rather than understood, and the alternative ordering — linkers before traps — puts
three chapters of file format between you and the first interesting thing the machine does.

## Where to start

[ch04](#ch04), in order, and this is the one part of the book with no routing in it. Each chapter's
machine is the previous chapter's machine plus one mechanism, and each program is the previous
program extended. Skipping ahead means reading code that assumes work you have not done.

## Which machine, and what it cannot tell you

`qemu-system-riscv64` with no firmware and no kernel: your program is the first thing the processor
executes. That is the right instrument for this part, because what it is faithful about is
*semantics* — a trap either lands where the vector register says it does or it does not, and QEMU
is exact about that.

**Nothing here is timed, and nothing in it may be**, for the reason [Part I](#part1) gives. There
is a second limit as well, particular to running with no operating system: QEMU is not silicon. A
real board has firmware that ran before your code ever started, errata, and a reset sequence more
complicated than the idealised one here. This part teaches the architecture, not any specific chip,
and a program from it will not boot a physical board unchanged.

## Where this leaves you

Holding a small machine you built yourself, and the vocabulary [Part IV](#part4) uses without
introducing.
