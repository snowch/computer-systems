---
title: "05 · Reading C as Machine Code"
short_title: "05 · Reading C as Machine Code"
---

(c-for-people-who-will-read-a-kernel)=
# 05 · Reading C as Machine Code

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch04](#c-without-a-runtime) |
| **Evidence** | RISC-V instructions emitted for reads, `volatile`, array parameters and indirect calls. |
:::

## The question

Which C constructs change the instructions, and which give information only to the compiler?

Compare pairs of C functions with their generated RISC-V instructions. Look for the difference
between reading memory, following a pointer and determining a name's visibility.

(c-for-people-who-will-read-a-kernel-example)=
## Compare C expressions with compiler output

(everything-here-is-an-address)=
### What a pointer designates

A pointer is a typed value that can designate an object or function, or can be null. Here,
a pointer to an object holds its address in byte-addressed memory. Its type tells the compiler,
for example, how to interpret the bytes of an integer at that address. [ch03](#memory-is-one-array)
introduces pointers and the limits on where they can point.

(volatile-the-one-qualifier-the-machine-has-heard-of)=
### Which reads does `volatile` preserve?

Two functions, identical but for one word — a *qualifier*, one of the words C lets you attach to
a type — each adding up four reads of the same address:

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

Find the load instruction in the plain listing and compare it with the four loads in the
`volatile` listing. Each loop iteration evaluates a separate read. In this example C treats
the volatile reads as observable and preserves the sequence of those evaluated accesses.

A device register can report a new value each time it is read. That is a reason to preserve
separate reads when the target defines a volatile interface for the device. C's `volatile`
qualifier provides neither atomic operations nor ordering between threads. Use the memory
ordering rules in [ch20](#locks-and-memory-ordering) for communication between hardware threads.

(an-array-parameter-is-a-promise-nobody-keeps)=
### What the function receives for an array parameter

```{literalinclude} ../sysfs/lib/addresses.c
:language: c
:start-at: /* `const int values[4]` looks like it promises four.
:end-before: int sysfs_sum_pointer
```

The declaration says four. The compiler discards that: an array parameter *is* a pointer, the
size in the brackets is documentation, and `sizeof` — the operator that gives a thing's size in
bytes — measures a pointer inside the function rather than an array. The proof is next to it in
the same file — `sysfs_sum_pointer` takes a plain pointer, does the same work, and compiles to
the same instructions:

```{include} _generated/c-for-people-who-will-read-a-kernel-array-parameter.md
```

A test in this repository asserts that the two are identical instruction for instruction, so if a
compiler ever stops agreeing, the claim fails rather than the sentence quietly becoming false.

An array is not a pointer, but it *decays* into one nearly everywhere: pass it, and what arrives
is an address. That is why kernel functions take a length alongside every
buffer, and why [ch13](#representing-information)'s bounds-check problem is a real bug pattern rather than an
invention.

### `static` — a word about who may know

```{literalinclude} ../sysfs/lib/addresses.c
:language: c
:start-at: /* Nothing outside this file can refer to this
:end-before: int sysfs_call_through
```

`static` on a function means *nothing outside this file may name this*. That is a statement to
the *linker* — the tool that joins compiled files into one program, met properly in
[ch15](#linking-and-loading) — and it has a consequence the compiler is quick to take advantage
of: if nobody outside can call it, then the compiler knows every call site, and may do whatever
it likes with them. Here is what it did:

```{include} _generated/c-for-people-who-will-read-a-kernel-private-call.md
```

There is no call. The helper was *inlined* — its body copied into the caller in place of a call —
and then deleted, and if you ask the object file for its symbols the helper is not among them. It
has stopped existing as a separate thing.

The keyword is overloaded and the two meanings are unrelated, which is a genuine wart. On a
function or a variable declared outside any function, `static` restricts *linkage* — who may
refer to it. On a variable inside a function, it changes *storage duration* — the variable
outlives the call and there is exactly one of it, for ever, shared by every caller. A kernel uses
both constantly and means something different each time.

### Calling through a variable

The last function. Instead of naming the one it calls, it takes it as an argument:

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

[ch19](#interrupts-and-drivers) uses this for real. [ch27](#the-cpu) comes back to it with a cost attached, because a
branch predictor faced with an indirect call has a much harder problem than one faced with a
direct one.

### Where it lives, and how long it stays

The three storage durations are worth knowing by their consequences rather than their names.

**Automatic** — an ordinary local. It lives in the current call's region of memory — its *stack
frame*, which [ch14](#machine-level-code-on-riscv) shows you — and it ceases to exist the moment
the function returns. A pointer to it, returned, is a pointer into space that the next call is
about to use for something else.

**Static** — a variable outside any function, or a local marked `static`. It exists for the whole
run of the program, there is exactly one, and *everybody shares it*. This is the one that produces
bugs that work perfectly until the second caller arrives, which is what this chapter's second
problem is.

**Allocated** — from `malloc`, or in a kernel from whatever the kernel has instead. It lives until
somebody says otherwise, and deciding who that somebody is has consumed more engineering time
than almost any other question this chapter raises.

xv6's kernel uses all three within a few hundred lines of each other, and reading it is much
easier once you are asking *which of these three is this* rather than *what does this pointer
mean*.

## What we measured

Nothing here is a cost. Every listing above is what one compiler emitted for one file, captured
by the machinery [ch12](#what-a-computer-does-with-a-program) explains and regenerated by CI on
each push.

Each one turns an assertion into something you can check: that a plain read may
be removed and a `volatile` one may not; that an array parameter and a pointer parameter produce
identical code; that a `static` helper can vanish entirely; and that calling through a variable
produces a different instruction from calling by name.

Those are facts about what the compiler *did*, and this chapter makes two other kinds of statement
as well. Claims about what C *permits* — that `volatile` forbids removing an access, that an
array parameter is adjusted to a pointer — are claims about the standard
@iso-c17 and would remain true on a compiler that produced entirely different output. Claims about
what any of it *costs* are not made at all.

## What this cannot tell you

**Whether an indirect call is expensive.** It is a different instruction, and this chapter shows
that much. Whether it costs more depends on whether the predictor can guess the target, which
depends on how many different functions actually flow through that call site at run time.
[ch27](#the-cpu) measures it; a chapter with no clock in it cannot.

**Whether `volatile` is what you want.** This chapter shows what it does — no access removed, no
access reordered with respect to another volatile access. It says nothing about whether that is
sufficient for your problem, and for anything involving two harts it is not. [ch20](#locks-and-memory-ordering) is
where that gets settled, and the answer involves instructions this chapter has not mentioned.

**What the optimiser will do with `static` next time.** The helper above was inlined because this
compiler judged it worthwhile. A larger one would not be, and the same source would then contain
a real call. "Static functions are free" is not a rule; "the compiler has more freedom with
static functions" is.

**How to write C.** Deliberately. This chapter covers what you need to *read* a kernel and stops
there — no style guidance, no idiom catalogue, and nothing about the parts of the language xv6
does not use.

## Problems

Use the files below in your local checkout. Run each test command from the repository root.

**5.1 — Which C produced this?**
Open `tests/c_for_people_who_will_read_a_kernel/problem_1_which_c.py`. Fill in `ANSWERS` to
match each listing to one source function. The test compiles the candidates locally. Compare
their loads, calls and returns with the listing when a match is wrong.

```bash
python3 -m pytest tests/c_for_people_who_will_read_a_kernel/test_problem_1_which_c.py
```

**5.2 — A function that works until it is called twice.**
Open `tests/c_for_people_who_will_read_a_kernel/scratchpad.c`. Change `describe` so both
returned strings survive two calls made before either string is used. Keep `main` as provided.
The test compares the two printed strings.

```bash
python3 -m pytest tests/c_for_people_who_will_read_a_kernel/test_problem_2_scratchpad.py
```

**5.3 — Build the table.**
Open `tests/c_for_people_who_will_read_a_kernel/problem_3_dispatch.py`. Fill in `TABLE`,
mapping each operation to its implementation in
`tests/c_for_people_who_will_read_a_kernel/devices.c`. Read the function bodies. The test
builds the table and checks each call’s result.

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
onto this book's chapters, and traces one system call through every layer both of them describe.
Start with `kernel/uart.c`, which is short and contains a `volatile` device register, a static
buffer with exactly the sharing problem this chapter's second problem describes, and a lock. You will not understand the lock yet. Read it anyway and come back after
[ch20](#locks-and-memory-ordering).

[Part II](#part2) is next, and it leaves the kernel behind: six chapters on a machine with
nothing on it, each building one mechanism — a trap, an interrupt, a page table — from the
hardware alone, before any kernel is read. Reading C as machine code resumes in
[ch14](#machine-level-code-on-riscv), which stops reading C and starts reading what it became:
registers, the calling convention, and a stack frame you can walk by hand.
