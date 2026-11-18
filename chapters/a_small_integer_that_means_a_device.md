---
title: "10 · A Small Integer That Means a Device"
short_title: "10 · A Small Integer That Means a Device"
---

(a-small-integer-that-means-a-device)=
# 10 · A Small Integer That Means a Device

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `bare` — a RISC-V machine in QEMU without an operating system |
| **Prerequisites** | [ch09](#a-system-call-of-your-own) |
| **Evidence** | Which devices receive `write`, and what changes in the descriptor table after `dup`. |
:::

## The question

Why does a program name what it reads by number, and what does that number find?

If you arrived from a language with a runtime, you have a picture of a file as an object: a thing
with methods, which knows how to read and write itself, and which you hold a reference to. The C
and Unix answer is stranger and much smaller. You hold an integer. The integer is not the file, does
not point at the file, and means nothing outside the program holding it.

This is where [Part I](#part1)'s claim — that everything is an index — arrives one level up.

(a-small-integer-that-means-a-device-example)=
## Follow a descriptor to an open file

### Two tables, and the difference between them

A *descriptor* — the integer — is an index into a table the kernel keeps for each process; here,
with no kernel, the machine-mode half of the program keeps it. What the table holds is not the
file either: it holds *which open file*, and the open file is a separate thing in a separate
table.

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: /* Two tables, and the distinction between them is the whole subject.
:end-before: static struct open_file *file_for(int fd)
```

Collapsing those two into one would be simpler and is the obvious first design. It is also wrong:
two descriptors can refer to one open file and share its position, which the last section of this
chapter shows.

### Two things worth having a table for

With one possible destination, an indirection demonstrates nothing: every descriptor would find the
same thing and the table would be decoration. So there are two *backends* — things a descriptor
can find. One is a real device at a physical address; the other is an array of bytes with a
cursor, which is a few lines long and is not a file system and is not pretending to be one.

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: /* The two things a descriptor can find.
:end-before: struct open_file {
```

The dispatch is a `switch`, and a third kind of backend would be one more case. The caller never
learns which backend it got.

### The same call, twice

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at:     /* 1. The same call, twice, differing in one register
:end-before:     cursor_after_writing = bare_call(SYS_TELL
```

Two calls, identical but for one number, and they end up in completely unrelated places — one in a
device register, one in an array in memory. Neither the calling code nor the compiler knows the
difference, which is how a shell can point a program's output at a file without the program being
told.

From your repository root, build and run the unedited descriptor demonstration:

```bash
./run descriptors
```

The console write prints `hello`. Then compare `cursor_after_writing`, `read_without_rewinding`
and `read_after_rewinding`. Which field shows where the memory write left the cursor? What
happens when a read begins at that position?

### The position is not a record of what you last did

Write six bytes into the array and the position is at six. So read them straight back:

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at:     /* 2. Read it straight back, without moving the cursor.
:end-before:     /* 3. Move the position, then read.
```

It returns nothing. Not an error, not a short read — zero bytes, from a call that is plainly
correct and an array that plainly has six bytes in it.

A descriptor's position is **where you are in the open file**, not a note about whether you were
last reading or writing, and that is the one thing about descriptors that catches everybody. The
write left it at the end, and the end is where the read started, and after the end there is
nothing. There is no separate read position to fall back on, because there is no separate read
position at all.

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at:     /* 3. Move the position, then read.
:end-before:     /* 4. A descriptor nobody opened.
```

Same descriptor, same array, same call — and six bytes this time, because the position moved
first. `read` and `write` here are the same two lines apart from which direction the bytes go:

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: /* Reads move the cursor exactly as writes do
:end-before: /* Where a descriptor currently is
```

### What `dup` shares

`dup` copies a descriptor onto another number, and it is the reason the two tables had to be two:

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at: static uint64 duplicate(int fd, int onto)
:end-before: uint64 bare_syscall
```

One number is copied. The open file it refers to is not — so afterwards two descriptors are two
names for one thing, and they share its position.

You can watch that happen rather than take it on trust. Six bytes have been written
through descriptor 2; the program duplicates it onto 3 and writes one byte through the copy:

```{literalinclude} ../sysfs/bare/descriptors.c
:language: c
:start-at:     /* 5. Duplicate, then write through the copy.
:end-before:     /* 6. And read the whole thing back
```

The byte lands at offset six, the position ends at seven, and reading the array back gives seven
bytes. Had the position lived in the descriptor instead, the duplicate would have started from
zero and written its byte over the `h` — both programs would still run, and the difference would
surface much later as a file mysteriously overwriting itself from the beginning.

**That shared position is the whole reason a second write continues rather than overwrites.** Two
descriptors onto one open file share one offset, so the write picks up where the last one left
off — a consequence of where the position already was, not a mode the write asks for.

## What we measured

These are the observations from the original program. Compare `dup_shares_the_open_file`
and `cursor_after_dup_write` with the earlier cursor position. Which observation shows that
the two descriptors share a position?

```{include} _generated/a-small-integer-that-means-a-device-descriptors.md
```

## What this cannot tell you

**Anything about cost.** A `write` here is a function call behind a trap. On a real system it is a
trap, a permission check, a copy from the program's memory into the kernel's, and possibly a
device. [ch29](#the-os-layers-cost) prices the real one.

**What an open file really contains.** A kind and a cursor is the smallest thing that shows the
sharing. A real one has a mode, a reference count, a position that several processes may be
contending over, and a pointer to something that knows how to be read. [ch22](#the-file-system) is
that, in a kernel.

**How the table gets entries.** There is no `open` here, because there is nothing to open: the two
backends are set up before the program starts. So the most interesting question about
descriptors — how a name becomes a number — is entirely absent, and [ch22](#the-file-system)
answers it.

**What the numbers 1 and 2 mean.** They mean what the two lines in `main` say they mean. On a real
system 0, 1 and 2 are a convention held up by the program that started you, not by the kernel, and
the convention is worth exactly as much as everyone's agreement to keep it.

## Problems

Use the files below in your local checkout. Run each test command from the repository root.

**10.1 — Duplicate onto a number in use.**
Open `tests/a_small_integer_that_means_a_device/problem_1_onto_open.py`. State your policy for
duplicating onto an open descriptor. Apply it in
`tests/a_small_integer_that_means_a_device/answer_onto.c`, starting from
`sysfs/bare/descriptors.c`. The test checks the reported target and asks you to justify the
result.

```bash
python3 -m pytest tests/a_small_integer_that_means_a_device/test_problem_1_onto_open.py
```

**10.2 — Add a third backend.**
Open `tests/a_small_integer_that_means_a_device/problem_2_third_backend.py`. Add the backend
in `tests/a_small_integer_that_means_a_device/answer_third.c`, starting from
`sysfs/bare/descriptors.c`. The new destination discards writes and returns no data on a read.
Report the fields specified in the stub for each destination.

```bash
python3 -m pytest tests/a_small_integer_that_means_a_device/test_problem_2_third_backend.py
```

**10.3 — Put the cursor in the wrong place.**
Open `tests/a_small_integer_that_means_a_device/problem_3_wrong_place.py`. Explain what breaks
when each descriptor has its own cursor. Make the change to a copy of
`sysfs/bare/descriptors.c` at `tests/a_small_integer_that_means_a_device/answer_cursor.c`. The
test checks the positions printed after duplicating and reading.

```bash
python3 -m pytest tests/a_small_integer_that_means_a_device/test_problem_3_wrong_place.py
```

## Where to go next

There is no specification for this one: a descriptor is not a hardware concept and nothing in the
RISC-V documents has heard of it. The nearest primary source is POSIX @posix-2018 on `dup` and
`write`, and it is worth reading `dup`'s wording specifically — the standard is careful about what
is shared in a way that only makes sense once you have built the two tables.

[ch11](#fork-built-rather-than-read) makes a second process, and the first question it has to
answer is which of these two tables the child gets a copy of.
