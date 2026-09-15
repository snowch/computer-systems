---
title: "fork, Built Rather Than Read"
short_title: "09 · fork, Built Rather Than Read"
---

(fork-built-rather-than-read)=
# 09 · fork, Built Rather Than Read

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [ch08](#a-small-integer-that-means-a-device) |
| **What it measures** | Two address spaces from one, a return value that differs between them, and the count of pages copied — beside what xv6 copies for the same call. |
:::

## The question

What is the least a machine needs before two programs can run on it?

`fork` is usually introduced as a riddle: a function that returns twice, with different answers. It
is not a riddle, and the reason it looks like one is that it is normally met from the outside. From
the inside it is a short function, and the two returns stop being mysterious the moment you can see
what a return actually is.

Everything this chapter needs already exists. [ch06](#one-page-table-two-harts) built an address
space; [ch07](#a-system-call-of-your-own) saved a caller's registers into a frame. A process is
those two things kept together, and `fork` is a copy.

## The material

### What a process is, here

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: struct proc {
:end-before: static struct proc procs
```

A saved register set, a place it was, and an address space. That is the whole of it — and the first
field is [ch07](#a-system-call-of-your-own)'s trap frame, unchanged. The frame was built to survive
a system call; keep it a little longer and it is a saved process.

### Mapping one page rather than one gigabyte

ch06 got away with three top-level leaf entries. A per-process page needs a real walk, because four
kilobytes is a leaf at the bottom level, and the levels above it have to exist first:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: /* Walk to the leaf entry for one virtual address
:end-before: static uint64 *build_address_space
```

Each process gets the kernel's identity mappings — without them the code would vanish the moment
its own table was installed — plus one page of its own at the same virtual address:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: static uint64 *build_address_space(uint64 *user_page)
:end-before: static int fork_current
```

Same address in both processes, different physical page behind it. That is what "its own memory"
means, mechanically, and it is the whole reason an address space is a useful thing to have.

### fork

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: static int fork_current(uint64 *frame)
:end-before: uint64 bare_syscall
```

The frame is copied wholesale and then one slot is changed. That single line is the famous
behaviour: the child is going to resume by having its frame loaded back into the registers, and
slot ten is `a0`, which is where a system call's return value lives. Two frames, identical but for
one word, produce two returns with different answers.

Note what else is copied and what is not. The page is copied — a fresh page and a byte-for-byte
duplicate, so the child begins with everything the parent had and can then diverge. This is the
eager version, and it is what xv6's `uvmcopy` does too: a fresh page and a copy, per page, at the
moment of the call. [ch16](#page-faults-as-a-feature) is where that stops being necessary.

### Putting a process back on the processor

```{literalinclude} ../sysfs/bare/syscalls.c
:language: c
:start-at: /* Put a saved process back on the processor: its registers, and where it was.
:end-before: }
```

`sp` is loaded last for a reason that is obvious in hindsight: every other load is relative to it,
and a frame stops being addressable the instant you replace the pointer to it.

The scheduler is four lines, and calling it a scheduler is generous:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: void bare_process_left(void)
:end-before: int main(void)
```

Install the next process's address space, load its registers, `mret`. There is no policy, no
priority and no preemption — it runs the other one when the first gives up. [ch19](#scheduling-and-context-switches)
is where the interesting parts go back in.

### The kernel cannot simply dereference what it is given

One detail here is a genuine trap, and it cost a confusing hour:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at:     /* The handler runs in machine mode, and machine mode ignores `satp`.
:end-before:     default:
```

The handler runs in machine mode, and [ch06](#one-page-table-two-harts) established that machine
mode ignores `satp`. So an address the caller supplies is not an address the handler can use — and
on this board the particular number involved lands in a PCI window that answers every read with
ones, so the failure is not even a fault. It is a plausible-looking wrong answer.

A real kernel walks the caller's page table to translate by hand. That function is called `copyin`,
and this is why it exists.

## What we measured

Run it yourself before reading the table — the numbers below are what you should
see, and a figure you have reproduced is worth more than one you have been shown:

```bash
./run fork
```

```{include} _generated/fork-built-rather-than-read-fork.md
```

One page copied, for one page mapped. xv6 copies every mapped page of the parent the same way —
`kalloc` and `memmove` per page, no sharing — so the count here is small for the same reason the
program is small, not because the strategy differs.

## What this cannot tell you

**What `fork` costs.** Copying a page has a price, copying a thousand has a much larger one, and
the entire reason real kernels stopped doing this eagerly is a number this target cannot produce.
[ch27](#the-os-layers-cost) measures a real `fork`, and the gap between an eager copy and what
Linux actually does is most of the answer.

**What the child should inherit.** The child here gets the address space and nothing else, because
there is nothing else. A real `fork` has to decide about descriptors, the working directory,
signal handlers, resource limits and more — and [ch08](#a-small-integer-that-means-a-device) built
the two tables that make the descriptor half of that question askable: the table is copied, the
open files it refers to are shared.

**Whether two processes really run concurrently.** They do not. One runs, gives up, and the other
starts. Nothing here preempts anything, and both are on one hart.

**What happens when the table is full.** There is room for two, `fork` is called once, and the
question of what a process table does when it runs out is left entirely alone. xv6's `allocproc`
returns zero; what the caller should do about it is a design question this program never has to
face.

## Problems

**9.1 — Make the child run first.**
The parent continues and the child waits. Swap it, so the child runs to completion before the
parent resumes, without changing what either prints. The test checks the order and that both still
report correctly.

```bash
python3 -m pytest tests/fork_built_rather_than_read/test_problem_1_child_first.py
```

**9.2 — Run out of processes.**
Call `fork` until the table is full. Decide what it returns then, implement it, and show the caller
handling it. The test checks the failure is distinguishable from a successful `fork` and that the
machine survives it.

```bash
python3 -m pytest tests/fork_built_rather_than_read/test_problem_2_full_table.py
```

**9.3 — Count what a lazy fork would save.**
Do not implement copy-on-write. Instead, say exactly which of this program's steps it would remove,
what it would add, and what new trap the handler would have to deal with. The test asks for the
cause code of that trap and for which page-table bit changes, both of which you have met.

```bash
python3 -m pytest tests/fork_built_rather_than_read/test_problem_3_lazy.py
```

## Where to go next

The privileged specification @riscv-isa-privileged has the page-table entry bits this program sets by hand,
including the one problem 9.3 asks about.

This is the end of [Part II](#part2). [Part III](#part3) steps back to ask what a program *is*
before [Part IV](#part4) reads a kernel — and that kernel's `fork` will look like a longer version
of this one rather than a new idea, which was the point of building it.
