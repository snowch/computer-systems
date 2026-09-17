---
title: "One Page Table, Two Harts"
short_title: "08 · One Page Table, Two Harts"
---

(one-page-table-two-harts)=
# 08 · One Page Table, Two Harts

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [ch07](#interrupts-and-privilege) |
| **What it measures** | One mapping installed by hand and an address that means something else afterwards; and a counter two harts disagree about. |
:::

## The question

What does address translation do, and what does a second core break?

Two questions, and two programs, because they are two mechanisms and a chapter that ran them
together would be teaching neither. What joins them is that both are things the hardware does to
memory behind the program's back — one deliberately and usefully, one as a consequence of there
being more than one processor.

## The material

### An address is a number until something translates it

Everything so far has used addresses that were what they said. `&marker` was where `marker`
actually was; the UART (the console's serial device) was at the number the board's documentation gives. Translation makes that
stop being true, and the whole of the mechanism is a table the program writes and a register that
points at it.

Sv39 splits a thirty-nine-bit address into three nine-bit indexes and a twelve-bit offset, which
means three levels of table. This program needs none of that, because an entry at the top level
can be a *leaf* — covering a whole gigabyte at once:

```{literalinclude} ../sysfs/bare/paging.c
:language: c
:start-at: /* A leaf entry for a whole gigabyte.
:end-before: static void build_the_table
```

The entire table is three entries:

```{literalinclude} ../sysfs/bare/paging.c
:language: c
:start-at: static void build_the_table(void)
:end-before: /* Runs with translation on.
```

Two of them map memory to itself. They have to: the moment translation is switched on, the
instruction after the switch is fetched through the table, and a table without the code in it
would make the program vanish. The third is the interesting one — a different virtual address
pointing at the same physical memory, so that afterwards two addresses a gigabyte apart name one
byte.

```{figure} _figures/one-page-table-two-harts-alias.svg
:alt: Three gigapage entries: two identity mappings and one alias into RAM.
:width: 100%

Two entries send a gigabyte to itself, so the running program does not vanish the moment
translation comes on. The third is the whole demonstration.
```

Switching it on is one register and one instruction:

```{literalinclude} ../sysfs/bare/paging.c
:language: c
:start-at:     bare_csr_write(satp, SATP_SV39
:end-before:     bare_csr_write(mepc, (uint64)in_supervisor_mode);
```

`sfence.vma` is there because the processor is allowed to remember translations it has already
worked out, and is not obliged to notice that the table changed underneath it. Forgetting it gives
a program that works until it does not, which is among the least pleasant kinds of bug.

And then the part that catches everyone: **machine mode ignores `satp` entirely**. Translation
applies to supervisor and user mode; machine mode addresses are physical, always. So the program
has to leave machine mode before any of this means anything, which is why [ch07](#interrupts-and-privilege)
came first.

```{literalinclude} ../sysfs/bare/paging.c
:language: c
:start-at: /* Runs with translation on.
:end-before: int main(void)
```

### What a second core breaks

The second program has two processors in it, and one counter.

The usual way to show what goes wrong is to start both harts incrementing as fast as they can and
observe that the total comes out short. That works, sometimes, and teaches the wrong thing when it
does: it makes lost updates look like weather. The real claim is narrower and much more useful —
`counter = counter + 1` is a load, an add and a store, and *anything at all* happening between the
load and the store is enough.

So this loses an update on purpose, identically every run, by holding those three instructions
apart and letting the other hart finish entirely in the gap:

```{literalinclude} ../sysfs/bare/harts.c
:language: c
:start-at:     /* The three instructions of `counter = counter + 1`
:end-before:     /* The same shape, with an instruction that has no gap in it.
```

The other hart's whole increment happens inside one statement of this one. Both processors
incremented; the counter went up once.

Then the same shape with an instruction that cannot be interrupted part-way through, because it is
one instruction:

```{literalinclude} ../sysfs/bare/harts.c
:language: c
:start-at:     /* The same shape, with an instruction that has no gap in it.
:end-before:     bare_printf("harts second_hart_ran
```

Nothing is lost, and nothing about the schedule changed. What changed is that there is no longer a
moment at which the counter has been read but not yet written.

:::{warning} This proves atomicity, and atomicity is not ordering
The instruction fixed one thing: the read and the write of *this* counter cannot be separated. It
says nothing about whether the other hart sees this hart's earlier writes to anything else, or in
what order, and a program built on the assumption that it does will be wrong on real hardware in
ways this target cannot show you. [ch20](#locks-and-memory-ordering) is where the difference gets
its own chapter, and [ch28](#memory-ordering-on-real-hardware) is where it costs something.
:::

## What we measured

Run them yourself before reading the table — the numbers below are what you should
see, and a figure you have reproduced is worth more than one you have been shown:

```bash
./run paging
./run harts
```

```{include} _generated/one-page-table-two-harts-paging.md
```

```{include} _generated/one-page-table-two-harts-harts.md
```

The runner refuses a run in which `updates_lost` is anything but exactly one. That is deliberate
and it is the difference between a demonstration and a coincidence: if the handshake ever stopped
holding the read-modify-write open, the program would still boot, still print, and still look
convincing, while showing nothing at all.

## What this cannot tell you

**How expensive any of this is.** A page-table walk costs something, a translation cache exists to
avoid paying it, and two cores touching one cache line cost each other a great deal. None of that
is visible here. [ch25](#the-memory-hierarchy) and [ch28](#memory-ordering-on-real-hardware) are
those questions on hardware, and the second one is where the atomic instruction above stops
looking free.

**What actually happens when two real cores race.** The lost update here was arranged. On real
hardware the ordering is decided by store buffers, coherence traffic and a memory model, and the
answer is neither deterministic nor as simple as one update going missing. What transfers from
this chapter is the shape of the hazard, not its likelihood.

**Whether one atomic is enough.** It was here, for one counter. It is not a general answer: an
operation that cannot be split is not the same as a sequence of them that cannot be reordered, and
the second is what a lock needs.

## Problems

**8.1 — Map a page rather than a gigabyte.**
Change the alias to cover four kilobytes instead of a gigabyte. You will need the two levels this
chapter skipped. The test checks that the alias still reads the same byte *and* that the entry at
the top level is no longer a leaf.

```bash
python3 -m pytest tests/one_page_table_two_harts/test_problem_1_four_kilobytes.py
```

**8.2 — Break it on purpose.**
Remove one of the two identity mappings and predict, before running it, exactly which instruction
the machine fails on and with what cause. Then run it. The test compares your prediction with the
run.

```bash
python3 -m pytest tests/one_page_table_two_harts/test_problem_2_no_identity.py
```

**8.3 — Lose an update the other way round.**
The program loses the second hart's increment. Rearrange the handshake so it loses the first
hart's instead, without changing the counter's final value. Say which of the three instructions
moved. The test checks the value, the loss, and that you did not simply swap the two harts' code.

```bash
python3 -m pytest tests/one_page_table_two_harts/test_problem_3_other_way.py
```

## Where to go next

The privileged specification @riscv-isa-privileged defines Sv39, the page-table entry format and `satp`; the
unprivileged specification @riscv-isa-unprivileged defines the atomic instruction the second program leans
on. Both are worth having open — the entry format in particular is one diagram and this chapter
built it by hand.

[ch09](#a-system-call-of-your-own) turns the boundary this chapter crossed into an interface.
