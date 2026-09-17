---
title: "Part I — C, and what the machine does with it"
short_title: "Introduction"
---

(part1)=
# Part I · C, and what the machine does with it

:::{note} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [ch02](#reading-a-listing)–[ch05](#c-for-people-who-will-read-a-kernel) |
| **Target** | `xv6` — the teaching kernel under QEMU, with [ch02](#reading-a-listing) also compiling for the board's architecture |
| **Assumes** | [ch00](#prerequisites-and-setup), and fluency in some other language |
:::

## What this part is for

Four chapters. One of them teaches reading what a compiler produced, and the other three have
one job between them: enough C to read a kernel and change it, and no more.

That "no more" is a real limit rather than modesty. C is a large language and most of it never
appears in the code this book reads. A part that set out to cover the language would spend most of
its length on things you are never going to meet here, and would still not have taught the thing
that actually stops people — which is not syntax.

What stops people is the model. Your language was built to hide it: memory is one array of bytes,
everything in it has an index, and a type is mostly a statement about how wide a step is. Every
language has that underneath. Yours decided you did not need to see it; C decided you did.

This part is first because everything after it is written in C and half of it asks you to change
some. [Part II](#part2) builds the machine's primitives in C and its problems have you rewriting a
trap handler; [Part IV](#part4) reads a kernel; [Part V](#part5) compiles C and reads what came
out. None of those is an exercise in the language. All of them are impossible without the model.

## What it leaves out

Control flow, operators and functions. You already have these, and C spells them much as your
language does. Where it differs the chapters say so and move on.

The standard library, which is [ch04](#c-without-a-runtime)'s subject from the opposite direction: a kernel has
almost none of it, and the interesting question is what it does instead. Floating point, for the
same reason — the kernel does not use it, and why it does not is a better question than how it
works.

And the craft of C as a language you would *build something in*: ownership discipline, API design,
build systems, the long list of ways to invoke undefined behaviour. The problems in this book ask
you to change a program that exists and predict what the change does — which needs the model and
almost none of the craft. That is not a soft option; it is the whole of what the rest of the book
needs, and it is reachable in three chapters, which the craft is not.

## Where to start

Read the four in order. [ch02](#reading-a-listing) is short and assumes no C, and every chapter
after it puts a listing in front of you. If you already write C, [ch03](#memory-is-one-array) is
the memory model you already have — skim it rather than skip it, because
[ch04](#c-without-a-runtime) is where it stops being the C you know.

[ch03](#memory-is-one-array) does not open with pointers: it opens with one complete program that
prints four numbers, and the pointers arrive afterwards as a way of explaining numbers you have
already watched appear.

## Which machine, and what it cannot tell you

Most of this part is compiled for RISC-V and run on the xv6 kernel under QEMU; [ch02](#reading-a-listing)
also compiles for the board's architecture and runs nothing at all. Three of the
four chapters ask you to read the disassembly of code you wrote — [ch02](#reading-a-listing) for
both of the book's instruction sets, the other two for RISC-V.

**Nothing in this part is timed, and nothing in it may be.** QEMU models no cache, no branch
predictor, no store buffer and no memory latency, so a duration measured inside it is a fact about
the laptop running the emulator, not about the machine being emulated. The figures here are
therefore all structural — what a program printed, what instructions the compiler emitted — and the
question of what any of it *costs* is not asked until [Part V](#part5), on hardware that can
answer it.

## Where this leaves you

Not a C programmer. Able to read one, and to change one and say what the change will do — which is
the thing the rest of the book actually requires, and [Part II](#part2) starts requiring it
immediately.
