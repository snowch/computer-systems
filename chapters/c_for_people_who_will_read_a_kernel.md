---
title: "C for People Who Will Read a Kernel"
short_title: "03 · C for People Who Will Read a Kernel"
---

(c-for-people-who-will-read-a-kernel)=
# 03 · C for People Who Will Read a Kernel

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch11](#representing-information) |
| **What it measures** | What the compiler emits for each construct: `bench/results/addresses-riscv64.json` |
:::

## The question

Which parts of C are really about addresses, and how do I read them without flinching?

This is not a C tutorial and it does not cover the language. It covers the subset that becomes
visible in machine code, sorted by a single question: **has the machine heard of this?** Some of
C's most-argued-about constructs are instructions to the compiler that leave no trace at all.
One of them is a prohibition that survives into every single load. Telling those apart is what
makes kernel source readable, because a kernel is mostly the second kind.

## The material

### Everything here is an address

A pointer is not a mysterious thing. It is an integer that happens to be the number of a byte,
carrying a type that says how many bytes to take from there and how to read them. That is the
whole idea, and almost every difficulty with pointers is really a difficulty about one of three
other questions: *where does this live*, *how long does it stay there*, and *who else can reach
it*. This chapter is those three questions, plus the constructs C offers for answering them.

### `volatile` — the one qualifier the machine has heard of

Two functions, identical but for one word, each adding up four reads of the same address:

```{literalinclude} ../sysfs/lib/addresses.c
:language: c
:start-at: int sysfs_read_four(const int *slot)
:end-before: int sysfs_sum_array
```

The plain one:

```{include} _generated/c-for-people-who-will-read-a-kernel-plain-reads.md
```

One load. The compiler reasoned that nothing between the reads could change what is at that
address, so it read once and multiplied — and it was right, under the rules it is given.

The `volatile` one:

```{include} _generated/c-for-people-who-will-read-a-kernel-volatile-reads.md
```

Four loads, in order, none of them removed.

`volatile` does not mean *shared*, it does not mean *atomic*, and it is not a threading
primitive — [ch18](#locks-and-memory-ordering) is emphatic about that.

**If you arrived from Java, this is the trap.** Java's `volatile` *is* a threading primitive: it
orders accesses between threads and the language's memory model defines what that guarantees.
C's does none of that. It constrains the compiler and says nothing whatever to the hardware, so
two harts can still see these writes in an order neither of them wrote. The keyword is spelled
the same and does a different job, and the instructions that do the other job are
[ch18](#locks-and-memory-ordering)'s. It means one thing: **every access in the source
must appear in the output, and in this order.** That matters when reading the address is not
merely reading memory. A device register that returns the next byte of a serial port gives a
different answer each time it is read, and a compiler that reads it once and reuses the value has
turned your driver into a program that receives one character forever. [ch17](#interrupts-and-drivers) writes that
driver.

This is why kernel source is full of a keyword that application code almost never needs. The
kernel is the layer where memory is not always memory.

### An array parameter is a promise nobody keeps

```{literalinclude} ../sysfs/lib/addresses.c
:language: c
:start-at: /* `const int values[4]` looks like it promises four.
:end-before: int sysfs_sum_pointer
```

The declaration says four. The compiler discards that: an array parameter *is* a pointer, the
size in the brackets is documentation, and `sizeof` inside the function measures a pointer rather
than an array. The proof is next to it in the same file — `sysfs_sum_pointer` takes a plain
pointer, does the same work, and compiles to the same instructions:

```{include} _generated/c-for-people-who-will-read-a-kernel-array-parameter.md
```

A test in this repository asserts that the two are identical instruction for instruction, so if a
compiler ever stops agreeing, the claim fails rather than the sentence quietly becoming false.

An array is not a pointer, but it *decays* into one nearly everywhere: pass it, and what arrives
is an address. The consequences are the reason kernel functions take a length alongside every
buffer, and the reason [ch11](#representing-information)'s bounds-check problem is a real bug pattern rather than an
invention.

### `static` — a word about who may know

```{literalinclude} ../sysfs/lib/addresses.c
:language: c
:start-at: /* Nothing outside this file can refer to this
:end-before: int sysfs_call_through
```

`static` on a function means *nothing outside this file may name this*. That is a statement to
the linker, and it has a consequence the compiler is quick to take advantage of: if nobody
outside can call it, then the compiler knows every call site, and may do whatever it likes with
them. Here is what it did:

```{include} _generated/c-for-people-who-will-read-a-kernel-private-call.md
```

There is no call. The helper was inlined and then deleted, and if you ask the object file for its
symbols the helper is not among them. It has stopped existing as a separate thing.

The keyword is overloaded and the two meanings are unrelated, which is a genuine wart. On a
function or a file-scope variable, `static` restricts *linkage* — who may refer to it. On a
variable inside a function, it changes *storage duration* — the variable outlives the call and
there is exactly one of it, forever, shared by every caller. A kernel uses both constantly and
means something different each time.

### Calling through a variable

The last pair. Instead of naming the function, take it as an argument:

```{literalinclude} ../sysfs/lib/addresses.c
:language: c
:start-at: int sysfs_call_through
```

```{include} _generated/c-for-people-who-will-read-a-kernel-indirect-call.md
```

The jump goes to a register. The target is not in the instruction; it was loaded, and the CPU
cannot know where this is going until that load has completed. That is the difference between a
direct and an indirect call, and it is the mechanism behind the pattern every operating system
uses to talk to hardware it has never heard of:

```{figure} _figures/c-for-people-who-will-read-a-kernel-dispatch.svg
:alt: A table of function pointers, each slot holding an address of code stored elsewhere.
:width: 100%

A table of function pointers. The kernel indexes it; the device supplies it.
```

A filesystem, a device driver and a network protocol all want the kernel to call *their* code
when something happens. None of them can be named in the kernel's source, because they may be
loaded later. So the kernel declares the shape of the table and each of them fills one in, which
is how one `read()` reaches a disk, a socket and a console.

[ch17](#interrupts-and-drivers) uses this for real. [ch25](#the-cpu) comes back to it with a cost attached, because a
branch predictor faced with an indirect call has a much harder problem than one faced with a
direct one.

### Where it lives, and how long it stays

The three storage durations are worth knowing by their consequences rather than their names.

**Automatic** — an ordinary local. It lives in the current stack frame and it ceases to exist the
moment the function returns. [ch12](#machine-level-code-on-riscv) shows you the frame. A pointer to it, returned, is a
pointer into space that the next call is about to use for something else.

**Static** — a file-scope variable, or a local marked `static`. It exists for the whole run of the
program, there is exactly one, and *everybody shares it*. This is the one that produces bugs that
work perfectly until the second caller arrives, which is what this chapter's second problem is.

**Allocated** — from `malloc`, or in a kernel from whatever the kernel has instead. It lives until
somebody says otherwise, and deciding who that somebody is has consumed more engineering time
than any other question in this chapter.

xv6's kernel uses all three within a few hundred lines of each other, and reading it is much
easier once you are asking *which of these three is this* rather than *what does this pointer
mean*.

## What we measured

Nothing here is a cost. Every listing above is what one compiler emitted for one file, captured
by the same machinery [ch10](#what-a-computer-does-with-a-program) introduced and regenerated by CI on each push.

What they establish is a set of claims that would otherwise be assertions: that a plain read may
be removed and a `volatile` one may not; that an array parameter and a pointer parameter produce
identical code; that a `static` helper can vanish entirely; and that calling through a variable
produces a different instruction from calling by name.

Those are facts about what the compiler *did*, and this chapter is careful to distinguish them
from two other kinds of statement it also makes. Claims about what C *permits* — that `volatile`
forbids elision, that an array parameter is adjusted to a pointer — are claims about the standard
@iso-c17 and would remain true on a compiler that produced entirely different output. Claims about
what any of it *costs* are not made at all.

## What this cannot tell you

**Whether an indirect call is expensive.** It is a different instruction, and this chapter shows
that much. Whether it costs more depends on whether the predictor can guess the target, which
depends on how many different functions actually flow through that call site at run time.
[ch25](#the-cpu) measures it; a chapter with no clock in it cannot.

**Whether `volatile` is what you want.** This chapter shows what it does — no access removed, no
access reordered with respect to another volatile access. It says nothing about whether that is
sufficient for your problem, and for anything involving two harts it is not. [ch18](#locks-and-memory-ordering) is
where that gets settled, and the answer involves instructions this chapter has not mentioned.

**What the optimiser will do with `static` next time.** The helper above was inlined because this
compiler judged it worthwhile. A larger one would not be, and the same source would then contain
a real call. "Static functions are free" is not a rule; "the compiler has more freedom with
static functions" is.

**How to write C.** Deliberately. This chapter covers what you need to *read* a kernel and stops
there — no style guidance, no idiom catalogue, and nothing about the parts of the language xv6
does not use.

## Problems

Three, and all three are about the loop this chapter is really teaching: change the source, look
at the output.

**3.1 — Which C produced this?**
Four listings and four candidate functions, matched up. The listings are not stored in the
repository: the test compiles each candidate with your toolchain and hands you what came out, so
the puzzle is generated rather than transcribed. Solving it by eye is possible. Solving it by
compiling each candidate and comparing is the point.

```bash
python3 -m pytest tests/c_for_people_who_will_read_a_kernel/test_problem_1_which_c.py
```

**3.2 — A function that works until it is called twice.**
`tests/c_for_people_who_will_read_a_kernel/scratchpad.c` turns a number into text and is correct in isolation. Called twice
before either answer is used, it is not. Fix it so both answers survive, changing anything you
like about the function and nothing about `main`.

The C library did exactly this for years, and some of it still does — which is why several
standard functions have an `_r` on the end.

```bash
python3 -m pytest tests/c_for_people_who_will_read_a_kernel/test_problem_2_scratchpad.py
```

**3.3 — Build the table.**
Four device operations and four functions that implement them. Put each function in the right
slot; the test builds a dispatch table from your answer, calls through it, and checks the
results. Read what the functions in `tests/c_for_people_who_will_read_a_kernel/devices.c` *do* rather than what they are called,
because one of the names is a trap.

Getting the declaration of a table of function pointers right is most of the exercise, and it
reads badly the first several times. That is not you.

```bash
python3 -m pytest tests/c_for_people_who_will_read_a_kernel/test_problem_3_dispatch.py
```

## Where to go next

The C standard @iso-c17 is the authority on which of this chapter's claims are about the language
rather than about a compiler — in particular §6.7.6.3 on the adjustment of array parameters, and
§6.7.3 on what `volatile` requires.

xv6's own source @xv6-riscv-source is now worth opening, and this is the chapter that makes it
possible. Its own commentary @xv6-book, written by the people who wrote the kernel and given away
by MIT, is the best explanation of what that code does; [Appendix G](#appendix-g) maps its topics
onto this book's chapters, and traces one system call through every layer both of them describe. Start with `kernel/uart.c`, which is about a hundred lines and contains a `volatile`
device register, a static buffer with exactly the sharing problem this chapter's second problem
describes, and a lock. You will not understand the lock yet. Read it anyway and come back after
[ch18](#locks-and-memory-ordering).

[ch12](#machine-level-code-on-riscv) stops reading C and starts reading what it became: registers, the calling
convention, and a stack frame you can walk by hand.
