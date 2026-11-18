---
title: "Part I · C, and what the machine does with it"
short_title: "Introduction"
---

(part1)=
# Part I · C, and what the machine does with it

:::{note} Part prerequisites and target
:class: chapter-header

| | |
|---|---|
| **Chapters** | [ch02](#reading-a-listing)–[ch05](#c-for-people-who-will-read-a-kernel) |
| **Target** | A local C compiler, RISC-V and AArch64 listings, and `xv6` under QEMU. |
| **Assumes** | [ch00](#prerequisites-and-setup), and fluency in some other language |
:::

## What this part is for

Read compiler output and connect it to C declarations, addresses and function calls. Later
parts use these ideas to explain why a kernel moves or saves particular values.

## What it leaves out

The examples assume you can already use conditionals, functions and operators in another
language. They introduce the C needed to read the examples. [ch04](#c-without-a-runtime)
explains what xv6 supplies for itself when normal application libraries are absent.

## Where to start

Start with [ch02](#reading-a-listing) to learn how to read a listing. In [ch03](#memory-is-
one-array), run the full C program on your computer, edit an initial value and compare the
printed values and byte offsets.

## Which machine, and what it cannot tell you

Use a local C compiler for the first run in [ch03](#memory-is-one-array). The material also
uses recorded RISC-V and AArch64 listings and the xv6 build. The instructional examples here
are never timed.

## Where this leaves you

You can read a declaration, predict what code does with its address and check that prediction
against a terminal run or the instructions a compiler emits.
