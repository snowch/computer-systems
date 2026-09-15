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
| **Chapters** | [ch01](#memory-is-one-array)–[ch03](#c-for-people-who-will-read-a-kernel) |
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Assumes** | [ch00](#prerequisites-and-setup), and fluency in some other language |
:::

## What this part is for

Three chapters and one job: enough C to read a kernel and change it, and no more.

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

The standard library, which is [ch02](#c-without-a-runtime)'s subject from the opposite direction: a kernel has
almost none of it, and the interesting question is what it does instead. Floating point, for the
same reason — the kernel does not use it, and why it does not is a better question than how it
works.

And the craft of C as a language you would *build something in*: ownership discipline, API design,
build systems, the long list of ways to invoke undefined behaviour. The problems in this book ask
you to change a program that exists and predict what the change does — which needs the model and
almost none of the craft. That is not a soft option; it is the whole of what the rest of the book
needs, and it is reachable in three chapters, which the craft is not.

## Where to start

**If you already write C**, start at [ch02](#c-without-a-runtime). ch01 is the on-ramp and you do not need it.
ch02 is about the habits that stop working when there is no library underneath you, and it is
written for you.

**If you program fluently in something else and have never written C**, start at
[ch01](#memory-is-one-array). You are not being taught to program.

**If you have tried C before and bounced off pointers**, also start at ch01, and notice that it
does not open with them. It opens with one complete program that prints four numbers, and the
pointers arrive afterwards as a way of explaining numbers you have already watched appear.

## Which machine, and what it cannot tell you

Everything here is compiled for RISC-V and run on the xv6 kernel under QEMU, and two chapters ask
you to read the disassembly of code you wrote.

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
