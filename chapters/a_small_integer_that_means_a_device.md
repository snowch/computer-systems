---
title: "A Small Integer That Means a Device"
short_title: "08 · A Small Integer That Means a Device"
---

(a-small-integer-that-means-a-device)=
# 08 · A Small Integer That Means a Device

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [ch07](#a-system-call-of-your-own) |
| **What it measures** | One `write` call reaching two unrelated destinations through one table, and the table itself printed before and after a descriptor is duplicated. |
:::

## The question

Why does a program name what it reads by number, and what does that number find?

If you arrived from a language with a runtime, you have a picture of a file as an object: a thing
with methods, which knows how to read and write itself, and which you hold a reference to. The C
and Unix answer is stranger and much smaller. You hold an integer. The integer is not the file, does
not point at the file, and means nothing outside the program holding it.

This is where [Part I](#part1)'s claim — that everything is an index — arrives one level up.

## The material

### Two tables, and the difference between them

A descriptor is an index into a table the kernel keeps for each process. What the table holds is
not the file either: it holds *which open file*, and the open file is a separate thing in a
separate table.

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: /* Two tables, and the distinction between them is the whole subject.
:end-before: static struct open_file *file_for(int fd)
```

Collapsing those two into one would be simpler and is the obvious first design. It is also wrong,
in a way that only shows up later — and the later is this chapter's last section.

### Two things worth having a table for

With one possible destination, an indirection demonstrates nothing: every descriptor would find the
same thing and the table would be decoration. So there are two. One is a real device at a physical
address; the other is an array of bytes with a cursor, which is about twenty lines and is not a
file system and is not pretending to be one.

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: /* The two things a descriptor can find.
:end-before: struct open_file {
```

The dispatch is a `switch`, and a third kind of backend would be one more case. That is the point
of the table: the caller never learns which it got.

### The same call, twice

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at:     /* The same call, twice, differing in one register.
:end-before:     read_back = bare_call(SYS_READ
```

Two calls, identical but for one number, and they end up in completely unrelated places — one in a
device register on a board, one in an array in memory. Neither the calling code nor the compiler
knows the difference. That is the entire value of the abstraction, and it is why a shell can point
a program's output at a file without the program being told.

### What `dup` shares

Now the reason the two tables had to be two:

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: static uint64 duplicate(int fd, int onto)
:end-before: uint64 bare_syscall
```

One number is copied. The open file it refers to is not — so afterwards two descriptors are two
names for one thing, and crucially they share one cursor. Six bytes written through the first and
one through the second leaves that single cursor at seven, which is a fact the program reports and
the runner refuses to accept a run without.

Had the cursor lived in the descriptor, `dup` would have produced two independent positions, both
programs would still run, and the difference would surface as a file mysteriously overwriting
itself.

## What we measured

```{include} _generated/a-small-integer-that-means-a-device-descriptors.md
```

## What this cannot tell you

**Anything about cost.** A `write` here is a function call behind a trap. On a real system it is a
trap, a permission check, a copy between address spaces, and possibly a device. [ch27](#the-os-layers-cost)
prices the real one.

**What an open file really contains.** A kind and a cursor is the smallest thing that shows the
sharing. A real one has a mode, a reference count, a position that several processes may be
contending over, and a pointer to something that knows how to be read. [ch20](#the-file-system) is
that, in a kernel.

**How the table gets entries.** There is no `open` here, because there is nothing to open: the two
backends are set up before the program starts. Which means the most interesting question about
descriptors — how a name becomes a number — is entirely absent, and is [ch20](#the-file-system)'s.

**What the numbers 1 and 2 mean.** They mean what the two lines in `main` say they mean. On a real
system 0, 1 and 2 are a convention held up by the program that started you, not by the kernel, and
the convention is worth exactly as much as everyone's agreement to keep it.

## Problems

**8.1 — Duplicate onto a number in use.**
`dup` here overwrites whatever was at the target. Decide what should happen when the target is
already open, implement it, and justify the choice. The test checks your behaviour is consistent
and that you did not simply refuse every duplicate.

```bash
python3 -m pytest tests/a_small_integer_that_means_a_device/test_problem_1_onto_open.py
```

**8.2 — Add a third backend.**
Add a destination that discards everything written to it and reads back as nothing. Show that the
calling code does not change. The test checks the caller is byte-identical across all three
descriptors.

```bash
python3 -m pytest tests/a_small_integer_that_means_a_device/test_problem_2_third_backend.py
```

**8.3 — Put the cursor in the wrong place.**
Move the cursor into the descriptor table and produce a program in which that change is visible in
the output. Say in one sentence which real-world behaviour would break. The test checks the shared
cursor claim now fails, and that your program shows it failing rather than asserting it.

```bash
python3 -m pytest tests/a_small_integer_that_means_a_device/test_problem_3_wrong_place.py
```

## Where to go next

There is no specification for this one: a descriptor is not a hardware concept and nothing in the
RISC-V documents has heard of it. The nearest primary source is POSIX @posix-2018 on `dup` and
`write`, and it is worth reading `dup`'s wording specifically — the standard is careful about what
is shared in a way that only makes sense once you have built the two tables.

[ch09](#fork-built-rather-than-read) makes a second process, and the first question it has to
answer is which of these two tables the child gets a copy of.
