---
title: "Kernel C Is Not Application C"
short_title: "04 · Kernel C Is Not Application C"
---

(c-without-a-runtime)=
# 04 · Kernel C Is Not Application C

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch03](#memory-is-one-array) |
| **What it measures** | What the kernel as built does not have: `bench/results/kernelc-xv6.json` |
:::

## The question

I already write applications — which of my habits stop working in a kernel?

The question is not about C, and you do not have to have written C to have the habits this chapter
is about: a Java or Python programmer holds more of them than a C one, not fewer, because more has
been done for them. Every assumption below is one an application programmer is entitled to make
in any language, and none of them holds here.

What goes wrong is not syntax; [ch03](#memory-is-one-array) covered that.

## The material

### One fact, and everything else follows from it

**There is nothing underneath you.** An application runs on a library, which runs on a kernel,
which runs on hardware. A kernel runs on hardware. Every difference in this chapter follows from
removing those two layers; read it that way rather than as a list.

Here is what removing them costs, counted from the kernel that is checked in.

```{include} _generated/c-without-a-runtime-absences.md
```

Three of those rows are what the rest of this chapter is about.

### No heap

There is no `malloc`, the library call an application makes when it wants memory, and no *heap*,
the region `malloc` hands memory out from. Nothing in the kernel defines either, and the row in
the table above is a count rather than a claim. The reason is an ordering problem rather than an
omission. `malloc` is built on a kernel's memory management, and this *is* the memory management.
It cannot call itself into existence.

So where do objects come from? Two places, and a kernel of this size uses both.

**A fixed array, decided when the kernel was compiled.**

```{include} _generated/c-without-a-runtime-pools.md
```

Every one of those is the length of an array that exists for the whole run. The kernel does not
allocate a process; it finds an unused slot in `proc[]` and marks it used. When there is no unused
slot, `fork` — the call that creates a process — fails, and *that* is what the limit means. A
reader used to allocation that either succeeds or raises has to get used to allocation that
returns a *null pointer* — a pointer whose value is zero, C's spelling of *nothing here* — and
expects the caller to check.

**A free list made of the free memory itself.** The other source is whole *pages* — the
fixed-size blocks the hardware divides memory into, and the unit it is handed out in. A list of
free pages needs a node per page, which would need memory, which is what we are trying to
allocate. The kernel resolves it by writing the link *into the free page*, because a free page by
definition holds nothing anybody wants.

```{literalinclude} ../xv6/xv6-riscv/kernel/kalloc.c
:language: c
:start-at: struct run {
:end-before: struct {
:caption: xv6, `kernel/kalloc.c` — MIT licence
```

That is [ch03](#memory-is-one-array)'s self-referential struct, and here it is doing real work.
This is the whole of what freeing a page does to it:

```{literalinclude} ../xv6/xv6-riscv/kernel/kalloc.c
:language: c
:start-at: r = (struct run *)pa;
:end-before: release(&kmem.lock);
:caption: xv6, `kernel/kalloc.c` — MIT licence
```

Cast the page's address to a `struct run *`, write the current head of the list into the page's
first bytes, and make the page the new head; allocating takes the head and follows the link it
finds there. Three lines of pointer arithmetic that would be undefined behaviour in an application
and are the allocator here — and one `acquire`, which is *Somebody else is running* below.
[ch18](#page-faults-as-a-feature) measures what it costs.

*Undefined behaviour* — the C standard's name for anything it declines to give a meaning to — is
not a figure of speech here. C is defined in terms of an *abstract machine*, the standard's own
model of what a C program does, written without reference to any real hardware. In that model a
pointer points at an *object*: something created by a declaration, or by an allocator, with a
lifetime the standard describes. `pa`, the address `kfree` was handed, is none of those. It is an
integer the kernel's build and the hardware agree is the address of usable memory, cast to a
pointer, and the abstract machine has no concept that would make the cast meaningful. Writing
through it is undefined not because it is dangerous but because the standard has nothing to say
about it.

It works anyway because the compiler is not the last word on this program. Declarations, objects
and lifetimes exist so that a compiler can reason about a program without asking the hardware;
here the hardware is the authority, and the kernel is asserting a fact about the machine that C
has no way to express. That is the real reason kernel C cannot be read as the C of the standard
with some library calls missing — it is the same language making a different bargain about who
decides what an address means.

### Memory that is not memory

An address in an application is somewhere your bytes are kept. In a kernel, some addresses are
wires. Writing a byte to one sends a character out of a serial port; reading one twice gives two
different answers because the second read consumes the next byte to arrive.

Every assumption a compiler makes about memory is wrong for those addresses — that reading twice
gives the same answer, that a read nobody uses can be dropped, that two writes to one place can be
combined into the last. `volatile`, a word put on the declaration, is how you withdraw those
assumptions, and [ch05](#c-for-people-who-will-read-a-kernel) shows the compiler obeying, one
instruction at a time.

This is why kernel source is full of a keyword application code almost never needs. `volatile` is
not defensive style; it is the difference between a *driver* — the part of a kernel that talks to
one device — and a program that receives one character for ever.

### Somebody else is running

An application with one thread has exclusive access to its own data by default. A kernel never
does: `NCPU` in the table of bounds above gives this machine eight harts, every one of them able
to be inside the same function as you, on data you are halfway through changing.

What that costs is [ch20](#locks-and-memory-ordering)'s subject and it is not small. When you read a
kernel structure, ask who else can reach it, and what stops them reaching it at the same moment
as you. That is not paranoia; it is the first question. `static` on a variable declared outside
any function does not make it yours — it hides the name from other *files*, and every hart runs
the same file.

### No floating point, on purpose

Zero instructions in the whole kernel name a floating-point register. That is a decision rather
than an oversight, and it is the kind of decision a kernel gets to make.

Floating-point registers are part of a process's state. Saving and restoring them on every
*context switch* — the moment the kernel stops running one process and starts another — costs
time on every switch, whether or not the process ever used one. xv6 declines: it does not save
them, so the kernel may not use them either, because a kernel that used one would corrupt
whichever process it interrupted. The cost of the feature is paid by everyone and the benefit
accrues to few, so the feature is not offered.

Real kernels make the same trade differently — usually by saving the registers lazily, the first
time a process touches one, which is [ch18](#page-faults-as-a-feature)'s mechanism used for
something other than memory.

### Almost no library, so the kernel writes its own

The table counts the functions this kernel reimplements because nothing supplies them: the string
and memory routines, and a formatted-print routine for the console. They are two short files,
the plainest complete C in the tree, and written in exactly the style
[ch03](#memory-is-one-array)'s second problem asked for — pointers that move, no subscripts, a
length passed alongside every buffer. Read them early.

The string copy is the example to notice. The standard `strncpy` takes a size and does not
promise to write the zero byte that ends a string; the kernel carries that one and, beside it,
`safestrcpy`, which takes a size and always writes it. When a kernel writes its own version of
something the library already has, the version usually differs on purpose, and the difference is
usually about a failure the library was willing to tolerate.

### Failure returns, it does not raise

There is no exception, no `finally`, no destructor and nothing to catch. A function that can fail
returns something you must look at, and a caller that does not look has written the bug.

This is the habit that takes longest to acquire, because in an application ignoring a failure is
usually survivable — something above you will notice. Here, nothing is above you. Problem 4.2 is
deciding which of several plausible kernel functions can fail at all, which is a question about
where their memory comes from — this chapter in one exercise.

### What C lets you do that you must not

C will not stop you. Neither will the hardware, until [ch18](#page-faults-as-a-feature). The three mistakes that cost
the most time, all of which compile without a word of complaint:

- **A pointer to a local — a variable in the current call's region — after the function
  returned.** The bytes are still there and still readable, right up until the next call writes
  over them, which is why this produces a bug that works in testing.
- **Reading or writing past the end of an array.** Nothing checks. [ch13](#representing-information) has the arithmetic
  that makes a bounds check look right and be wrong.
- **Two harts writing one variable with no lock** — nothing to make one wait for the other —
  which works perfectly until the machine is busy. [ch20](#locks-and-memory-ordering) is the chapter, and [ch28](#memory-ordering-on-real-hardware) is what it costs on real hardware.

## What we measured

What the kernel does not have, counted from the kernel that is checked in rather than asserted:
its instruction count, how many of those name a floating-point register, how many heap functions
it defines, how much of the C library it carries its own copy of, and the compile-time bounds that
stand in for an allocator.

`bench/run_kernelc.py` refuses to stamp a census in which the kernel has acquired floating point
or a heap. An absence is the weakest kind of claim to make and the easiest to go quietly stale, so
the two the chapter argues from are the two that fail CI when they stop being true.

## What this cannot tell you

**How a production kernel does any of this.** Linux has allocators, per-CPU data, lazy
floating-point saving and a great deal more. xv6's answers are the simplest ones that work, chosen
so they can be read, and reading them is what makes a bigger kernel's answers legible as choices
rather than as complexity.

**What any of it costs.** No clock in this part. The free list is [ch18](#page-faults-as-a-feature), locks are
[ch20](#locks-and-memory-ordering) and [ch28](#memory-ordering-on-real-hardware), and the context switch that declines to save floating-point
registers is [ch21](#scheduling-and-context-switches).

**Whether your kernel C is correct.** Nothing here is a checker. The habits in this chapter narrow
where to look; they do not tell you that you have looked hard enough, and the problems in [Part IV](#part4)
are about mechanisms that defeat careful reading entirely.

**Anything about C++ or freestanding C beyond this kernel.** "Freestanding" is a word the standard
@iso-c17 defines and this chapter has deliberately not used, because what actually matters is
which specific things are missing here, and that is a property of xv6 rather than of a
conformance mode.

## Problems

Three, in `tests/c_without_a_runtime/runtime.c`.

**4.1 — Hand out objects from a pool, and take them back.**
No allocator. A fixed array, a way to find an unused entry, and a way to return one. Getting the
"none left" case right is most of the exercise, because it is the case an application programmer
has never had to write.

```bash
python3 -m pytest tests/c_without_a_runtime/test_problem_1_pool.py
```

**4.2 — Which of these can fail?**
Several kernel functions described by where their memory comes from. Say which can fail and what
each must return when it does. The answer is never "it throws".

```bash
python3 -m pytest tests/c_without_a_runtime/test_problem_2_failure.py
```

**4.3 — What does a missing `volatile` cost?**
Given several loops over an address, say which the compiler may reduce and to what. One of them is
a driver that receives one character for ever.

```bash
python3 -m pytest tests/c_without_a_runtime/test_problem_3_volatile.py
```

## Where to go next

`kernel/string.c` and `kernel/kalloc.c` are the two files to read after this chapter — short
enough for one sitting, and containing every idea above. [Appendix D](#appendix-d) says what else
is in the tree and which chapter reads it.

[ch05](#c-for-people-who-will-read-a-kernel) is the last chapter of this part and the one that puts a compiler behind the claims.
It sorts C's constructs by a single question — has the machine heard of this? — and answers it
with disassembly rather than with assertion.
