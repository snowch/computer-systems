---
title: "Representing Information"
short_title: "11 · Representing Information"
---

(representing-information)=
# 11 · Representing Information

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch10](#what-a-computer-does-with-a-program) |
| **What it measures** | Type sizes, alignments and struct layouts, and what signed and unsigned arithmetic actually compile to: `bench/results/setup-xv6.json`, `bench/results/signedness-riscv64.json` |
:::

## The question

What is a number to this machine, and when does that answer bite?

Most of the time it does not bite at all, which is the difficulty. A machine word behaves enough
like an integer that a programmer can go years without meeting the difference, and then meet it
in production. So this chapter is organised around the places the representation *leaks* —
where two things that look identical in C turn out not to be, and the reason is always that one
of them made a promise the other did not.

## The material

### Two rules make every struct

[ch00](#prerequisites-and-setup) measured two structs with the same three members in different orders and found one
larger than the other. A table can say that. It cannot say where the extra bytes went, and that
is the part worth seeing:

```{figure} _figures/representing-information-padding.svg
:alt: Both structs drawn byte by byte, with the bytes no member uses marked.
:width: 100%

The holes are not at the end. They are wedged between members.
```

Two rules produce every gap in that picture:

1. **A member starts at a multiple of its own alignment.** A four-byte integer may begin at
   offset zero, four, eight — not at one. This is not the compiler being fussy: many machines
   load a word faster when it does not straddle two of them, and some refuse outright.
2. **A struct's size is a multiple of its own alignment**, which is the largest of its members'.
   Otherwise the second element of an array of them would start somewhere illegal.

And one prohibition that turns those rules into your problem rather than the compiler's: **C does
not permit members to be reordered** @iso-c17. The order you wrote is the order you get, and the
padding follows from it. Every other language with a struct-like type had this same choice to
make, and several of them chose differently.

On a single struct this is an oddity. On an array of a few million — a particle system, a packet
buffer, a page-table cache — it is the difference between fitting in a level of cache and not,
which is [ch23](#the-memory-hierarchy)'s subject and the first place this dry rule becomes a duration.

### A comparison that is not a comparison

Here are two functions. They differ by one word.

```{literalinclude} ../sysfs/lib/signedness.c
:language: c
:start-at: int sysfs_signed_grows
:end-before: int sysfs_signed_quarter
```

Both ask whether adding one to a number makes it bigger. This is what the compiler did with the
signed one:

```{include} _generated/representing-information-signed-grows.md
```

It does not add. It does not compare. It returns *yes* without looking at the argument, because as
far as the compiler is concerned there is no argument for which the answer could be anything else.

And the unsigned one:

```{include} _generated/representing-information-unsigned-grows.md
```

That one does the work.

The difference is not that unsigned arithmetic is slower. It is that **the two types make
different promises**. Unsigned overflow is defined: it wraps, and the largest unsigned value plus
one really is zero, so the comparison can be false and the compiler must ask. Signed overflow is
*undefined* @iso-c17 — the standard declines to say what happens — so a compiler is entitled to
assume it never occurs, and from that assumption `x + 1 > x` follows for every `x` that exists as
far as it is concerned.

This is the first appearance of a thing worth being permanently uneasy about. **Undefined
behaviour is not a runtime hazard; it is a licence the optimiser holds.** The danger is not that
your program will crash when it overflows. The danger is that a branch you wrote to check for
overflow will be deleted, because the compiler reasoned that the condition could not arise.

### A division that is not a division

The same pair again, dividing instead of adding:

```{literalinclude} ../sysfs/lib/signedness.c
:language: c
:start-at: int sysfs_signed_quarter
```

Unsigned first, because it is the one that behaves:

```{include} _generated/representing-information-unsigned-quarter.md
```

One shift. Dividing an unsigned number by a power of two *is* a right shift, exactly, with no
edge cases.

Signed:

```{include} _generated/representing-information-signed-quarter.md
```

Several instructions, and the extra ones are not arithmetic — they are a correction. An
arithmetic right shift rounds towards negative infinity; C requires integer division to round
towards zero @iso-c17. For positive numbers those agree. For negative ones they differ by one, so
the compiler adds a bias before shifting, and the bias has to be computed from the sign bit
because it only applies to negatives.

Nobody wrote that correction. It is the cost of a promise C made about rounding, paid on every
signed division by a constant, by a programmer who thought they were writing a shift.

**Neither of these functions is wrong, and neither compiler decision is a bug.** That is the point
of putting them side by side: the machine code you get is a consequence of the type you chose,
and the type is a claim about what values are possible. Make a weaker claim and you get more
instructions; make a stronger one and the optimiser will use it, including in ways you did not
intend.

### Byte order, seen rather than described

A number wider than a byte has to be laid out in memory somehow, and there are two sensible
answers. Both of this book's machines choose little-endian: the lowest-addressed byte holds the
least significant part. The probe asks the machine rather than asserting it, which is why the
fact appears in [ch00](#prerequisites-and-setup)'s output and not in a footnote here.

It matters in exactly three places, and outside them you can forget it: when bytes cross a
machine boundary (a file, a network, a device register), when you alias a value through a pointer
of a different width, and when you are reading a memory dump by eye and the digits appear to be
backwards. [ch17](#interrupts-and-drivers) meets the third kind for real, reading a device that does not agree with
the CPU about byte order.

### The operations worth writing once

`sysfs/lib/bits.c` holds the bit manipulations later chapters reuse. They are written out the
long way rather than calling a builtin, because this is the chapter where a machine word stops
being an abstraction, and a loop you wrote teaches that better than an intrinsic you called:

```{literalinclude} ../sysfs/lib/bits.c
:language: c
:start-at: unsigned sysfs_popcount
:end-before: unsigned long sysfs_reverse_bits
```

`word &= word - 1` clears the lowest set bit. It is worth learning as a shape rather than
deriving each time, and it is the single most reused identity in this book.

One thing in that file is not about bits at all:

```{literalinclude} ../sysfs/lib/bits.c
:language: c
:start-at: unsigned long sysfs_round_up_pow2
:end-before: int sysfs_is_aligned
```

The overflow check runs *before* the shift. Afterwards there is nothing left to notice by — the
bit has gone, and the value is zero, and zero is indistinguishable from a legitimate answer. That
ordering is the whole of the lesson in [ch22](#measuring) about checking for a condition while the
evidence still exists, arriving several chapters early because arithmetic is where it bites first.

## What we measured

The C implementation both targets present — sizes, alignments and byte order — is
[ch00](#prerequisites-and-setup)'s table, measured by booting the kernel and asking it. It is not repeated here,
because a figure printed twice is a figure that can disagree with itself.

What this chapter adds is the machine code above, and it is worth being clear about what kind of
evidence that is. Those listings are not timings and nothing in this chapter is. They are what
one compiler emitted for one source file at one optimisation level, regenerated by CI on every
push so that a compiler which changes its mind breaks the build rather than the argument.

Counting instructions is not measuring cost. A function with more instructions in it can be
faster than one with fewer, and [ch25](#the-cpu) shows a case where that happens for reasons
entirely outside the count. What the listings establish here is something weaker and more useful:
that the two functions in each pair are *not the same program*, whatever the source looked like.

## What this cannot tell you

**Whether any of it is slow.** Signed division emits a correction; whether that correction costs
a measurable amount depends on the core, on what else is in flight, and on whether the result was
needed immediately. [ch24](#optimising-code) is where that gets a number, on a machine that can produce one.

**What another compiler does.** Every listing here is one version of `gcc`. A different compiler
may fold differently, and the standard permits both. The claims about *what C says* are claims
about the standard @iso-c17 and are stable; the claims about what the machine code looks like are
claims about a toolchain and are stamped accordingly.

**What undefined behaviour will do to you.** This chapter shows one consequence — a comparison
compiled away — because it is visible in a disassembly. The full set is not enumerable, and
anyone who tells you the rule is "it does whatever the hardware does" has the wrong model: the
hardware never sees the code that was deleted.

**Floating point.** It is absent from this chapter and from the xv6 target generally, and that is
a decision rather than an oversight: xv6 does not save floating-point registers across a context
switch, so a user program that uses them is quietly wrong the moment it is descheduled. That is a
perfectly reasonable thing for a teaching kernel to decide — it makes [ch19](#scheduling-and-context-switches)'s context
switch small enough to read in one sitting — and it means floating point arrives in Part V,
on a machine whose kernel does save them.

## Problems

Three, and none of their answers is anywhere in this repository.

**2.1 — Two operations the library does not have.**
`tests/representing_information/bitops.c` asks for a byte-order swap and the index of the lowest set bit. Neither is
in `sysfs/lib/bits.c`, so there is nothing to copy. The test checks *properties* rather than
cases: swapping twice must give back what you started with, and the bit you name must be set with
nothing set below it. A property holds for every input, so it cannot be satisfied by memorising.

```bash
python3 -m pytest tests/representing_information/test_problem_1_bitops.py
```

**2.2 — Pack the struct.**
Five members, declared in an order that wastes space. Give the order that wastes least. The test
compiles your arrangement and compares it against the best that arrangement of those types can
do — it does not tell you the number, and the two rules at the top of this chapter are enough to
work it out.

```bash
python3 -m pytest tests/representing_information/test_problem_2_reorder.py
```

**2.3 — Find the input that makes it wrong.**
A bounds check that looks correct and is not. Find one triple of values where it says a read fits
and the read would run off the end.

Nothing in it is undefined: the type is `unsigned`, so the machine does exactly what it was told,
and the result is still wrong. That is the uncomfortable half of this chapter — undefined
behaviour is dramatic and rare, and *defined* behaviour that does not match your intention is
quiet and everywhere.

```bash
python3 -m pytest tests/representing_information/test_problem_3_break_it.py
```

## Where to go next

The C standard @iso-c17 is the document that decides which of this chapter's surprises are the
compiler's fault and which are yours. It is not readable end to end, and it is not meant to be —
but looking up one behaviour you thought you knew is a formative afternoon, and the freely
available committee draft is fine for that.

The RISC-V unprivileged specification @riscv-isa-unprivileged defines what the shift and division
instructions above actually do, including the cases C calls undefined. Reading the two documents
against each other is how you learn that "undefined behaviour" describes a *language*, not a
machine: the hardware always does something specific, and knowing what does not make the C legal.

The psABI @riscv-psabi fixes the sizes and alignments this chapter's structs are laid out by.

[ch03](#c-for-people-who-will-read-a-kernel) takes the other half of C — the part that is really about addresses — and does the
same thing to it.
