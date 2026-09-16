---
title: "Part II — The machine with nothing on it"
short_title: "Introduction"
---

(part2)=
# Part II · The machine with nothing on it

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch06](#a-trap-with-nothing-else)–[ch11](#fork-built-rather-than-read) |
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Assumes** | [Part I](#part1) |
:::

## What this part is for

Six chapters, each building one primitive of the machine with nothing else in the way.

The difficulty this part answers is real and it is the usual reason people stall on kernels. A
kernel presents its primitives already entangled. The first trap you meet in xv6 arrives with a
process table, a page table, a scheduler and a lock attached to it, and the code that handles it is
correct about all of them at once. You are asked to learn what a trap *is* from a page that assumes
you already know.

So: no kernel. No library, no loader, no operating system, nothing at the far end of a `printf`.
The machine comes out of reset and runs your instructions. Each chapter then adds exactly one
mechanism to a machine that has none — a trap, an interrupt, a page table, a system call, a
descriptor table with `read` and `write` over it, and finally a second process made from the
first.

They do not all come from the same place, and the division is the part's shape.
[ch06](#a-trap-with-nothing-else)–[ch09](#a-system-call-of-your-own) are things the *hardware*
hands you: a trap vector, a saved program counter and the instruction that returns from a trap are
in the privileged specification, not in anybody's kernel.
[ch10](#a-small-integer-that-means-a-device) and [ch11](#fork-built-rather-than-read) are not.
A descriptor table, and a second process made from the first, are inventions of software — no
hardware has heard of either — and that is exactly why they are built here instead of read about
later. A descriptor turns out to be an index into an array, and `fork()` turns out to be a copy;
neither needs an operating system to exist, and finding that out on a machine with no operating
system on it is the shortest route to believing it.

So the part sits before [Part IV](#part4) rather than inside it for two reasons, not one. The
hardware's mechanisms were never the kernel's to begin with. The software's are, and meeting them
without a kernel is how you learn there is nothing magic in them. Having written the three-instruction trap
handler yourself and watched it work changes what xv6's trap handling looks like: an arrangement of
things you have built, rather than a wall of new ideas.

## What it leaves out

Everything that makes a kernel a kernel. No scheduling policy, no file system, no device beyond the
one serial port needed to see anything at all, no allocator beyond what a page table requires.

What a descriptor *finds* — anything more than the two backends [ch10](#a-small-integer-that-means-a-device)
needs to make the indirection visible. There is no disk here and nothing to open, so the table
holds the serial port and a byte array with a cursor, which is enough to show that the calling
code does not change and not enough to be a file system. The several kinds of open file that make
a table of them worth keeping are [ch22](#the-file-system).

**A pipe**, and the reason is worth more than the pipe would be. A pipe is not a buffer; it is a
buffer plus what happens when the buffer is empty. The reader blocks, something else runs, and
somebody wakes them — and this machine's entire scheduler is *when a process leaves, put the next
one on*. It moves one way and never comes back, so a process here cannot wait for another and then
continue. What could be built is a shared array with a cursor, which is the easy half of a pipe and
teaches the wrong thing by leaving out the half that defines it. Blocking needs a scheduler that
can switch both ways, which is [ch21](#scheduling-and-context-switches), and sleeping and waking
are settled there.

And one thing it leaves out on purpose, which is worth saying plainly: **you will use a linker
script and read assembly here, and neither is explained until [Part III](#part3).** Treat them as
recipes. [ch14](#machine-level-code-on-riscv) covers the instructions and [ch15](#linking-and-loading) covers the script. This part needs
them working rather than understood, and the alternative ordering — linkers before traps — puts
three chapters of file format between you and the first interesting thing the machine does.

## Where to start

[ch06](#a-trap-with-nothing-else), in order, and this is the one part of the book with no routing in it. Each chapter's
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
