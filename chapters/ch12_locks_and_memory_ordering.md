---
title: "Locks and Memory Ordering"
short_title: "ch12 Locks and Memory Ordering"
---

(ch12)=
# ch12 · Locks and Memory Ordering

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch11](#ch11) |
| **What it measures** | What a lock is made of, in instructions: `bench/results/locks-xv6.json`, `bench/results/ordering-riscv64.json` |
:::

## The question

What breaks when two harts touch the same memory, and what is the minimum fix?

[ch11](#ch11) ended owing an answer. Its census counters are incremented from interrupt handlers
and from process context, on three harts, with no lock anywhere — and the patch says so in a
comment that amounts to *this is fine*. Either that is defensible or the book has been printing
numbers from a data structure that races, so this chapter has to settle it.

## The material

### A race is three instructions

The sentence "two threads incrementing a counter can lose an update" is usually offered as a fact
about threads. It is not. It is a fact about what an increment becomes:

```{include} _generated/ch12-race.md
```

Three instructions: load, add, store. Nothing in the machine holds them together. Another hart can
load between your load and your store, and then both of you store the same value — one increment
where there should have been two. An interrupt can land in the same gap on a single hart, which is
why this is not only a multiprocessor problem.

That is the whole mechanism. Everything else in this chapter is about closing that gap, and the
first thing worth noticing is that both architectures produce the same three instructions. The
problem does not belong to an instruction set.

### One instruction instead of three

The minimum fix is to ask the machine for an increment it will not interrupt:

```{include} _generated/ch12-atomic.md
```

On RISC-V that is `amoadd.d` — atomic memory operation, add, doubleword. One instruction, so there
is no gap to land in.

The AArch64 version is the surprise, and it is worth stopping on. Instead of an instruction there
is a **call** to a helper with a name the programmer never wrote. AArch64 gained single-instruction
atomics in a later revision of the architecture, so a compiler that does not know which chip it is
building for cannot use them directly; it emits a call to a routine that decides at run time.
Whether the same C is one instruction or a function call is therefore not a property of the source
or even of the architecture, but of what the compiler was told to assume.

[ch18](#ch18) is where being told matters.

### The ordering is not the atomicity

Two things are commonly rolled together and are separate. An operation can be *indivisible* and
still be reordered against its neighbours.

```{include} _generated/ch12-ordered.md
```

That is the same increment with the strongest ordering the language offers, and it is the same
single instruction with two letters added: `.aqrl`, acquire and release. **Ordering costs no extra
instruction here at all** — the atomic instruction carries its own ordering, and what would be a
separate fence on another machine is two bits of an opcode on this one.

So "an atomic operation" and "an ordered operation" are different requests, and on RISC-V you can
see that they are, because the spelling changes and the instruction count does not.

### Publishing something

The reason ordering matters separately from atomicity is the pattern every lock is built out of:
write something, then announce that you have written it.

```{include} _generated/ch12-publish.md
```

The RISC-V version writes the value, then `fence rw,w`, then writes the flag. The fence is doing
one job: it forbids the flag's store from becoming visible before the value's. Without it a reader
on another hart could see the flag set and the value stale, and every instruction involved would
have executed exactly as written.

AArch64 spells the same requirement as `stlr` — a store with release ordering built in, one
instruction instead of two. Same semantics, same guarantee, different arithmetic. A reader who
learned that "a barrier is an instruction you put between things" would not recognise the second
version as containing a barrier at all.

Compare it with the same code written without the ordering and the difference is one instruction
on RISC-V and none on AArch64 — where the plain version uses `str` and the ordered one `stlr`, so
the cost is not an instruction but a choice of instruction.

### What xv6's lock is made of

Now the kernel's own, disassembled as built rather than reimplemented for a book:

```{include} _generated/ch12-primitives.md
```

Three things in that table are worth reading carefully.

**One instruction in `acquire` does the mutual exclusion.** The atomic column says one, and the
instruction is `amoswap.w.aq` — swap a one in, and if what came out was already one, somebody else
holds it, so go round again. Everything else in those twenty-five instructions is xv6 checking
that the caller is not already holding the lock and panicking if it is. The lock is one
instruction; the rest is the kernel protecting you from yourself.

**`release` contains no atomic instruction at all.** Releasing is an ordinary store — there is
nobody to compete with, because you hold the lock. What it does contain is the fence, and that
fence is the entire reason the lock works: it is what stops the work you did inside the critical
section from becoming visible *after* the store that lets the next hart in.

**Turning interrupts off costs more than the lock does.** `push_off` and `pop_off` are, between
them, more instructions than `acquire` and `release` together. They exist because a lock held
across an interrupt on the same hart would deadlock against its own handler, and they are the
price of that safety rather than of the mutual exclusion.

### So was chapter 11 right?

Back to the debt.

[ch11](#ch11)'s counters are incremented without a lock from several harts and from interrupt
context. On the evidence above, that increment is three instructions and updates can certainly be
lost. **The patch is therefore wrong in the sense that its counts can be short, and right in the
sense that this is the correct trade.**

The argument is not "it is only a counter". It is that the alternative is worse in a way that
matters to this book specifically. A lock on the trap path is itself work on the trap path:
`push_off`, an atomic, a fence, `pop_off` — on every entry into the kernel, added to the thing
being measured. The measurement would change what it measures, and it would change it by an
amount of the same order as some of the things this book wants to count.

So the census is deliberately approximate where approximation is cheap, and the results that
matter — the ones in [ch10](#ch10) and [ch11](#ch11) — are the ones fixed by the workload rather
than accumulated under a race. That is a decision rather than an oversight, and it is the kind of
decision that should be written down where a reader can disagree with it.

## What we measured

Instruction counts, and what kinds of instruction they are, for the lock primitives in the kernel
as built and for five ways of incrementing a counter on two architectures. Nothing here was
executed and nothing was timed.

The plan for this chapter promised contention counts per lock, and said the interleavings would be
deterministic under QEMU. Neither survived contact. Contention is a statement about how long one
hart made another wait, which is a duration this target cannot supply — and the interleavings are
not deterministic either: [ch11](#ch11) had already found the console's interrupt count varying
between identical runs, which is the same emulator being the same amount of non-deterministic.
The chapter measures what is actually there instead, and this paragraph is here because a plan
that turned out to be wrong is worth more to a reader than a plan quietly rewritten.

## What this cannot tell you

**What a lock costs.** The whole of it. An uncontended acquire is one atomic instruction, and what
that instruction costs depends on whether the cache line is already held exclusively, which
depends on what the other cores have been doing. A contended one costs however long you waited.
Both are questions about hardware, and [ch20](#ch20) asks them on a machine that can answer.

**Whether the fence is doing anything here.** RVWMO permits the reorderings the fence forbids, and
QEMU is entitled to but does not perform them: it executes each hart's instructions in order.
So every program in this chapter would behave identically with the fences removed, on this target,
and would be broken on real hardware. That is an uncomfortable property of the instrument and the
reason problem 10.2 asks about the model rather than about a run.

**Anything about fairness.** xv6's lock is a plain spin: whoever's swap happens to succeed gets
in, and a hart can be unlucky indefinitely. Real kernels care, use queues and tickets, and pay for
them. None of that is visible in an instruction count.

**Sleep locks, which the chapter has not mentioned.** xv6 has them, they are what
[ch11](#ch11)'s console driver used, and they are built on top of the spinlock plus the scheduler
rather than beside it. [ch13](#ch13) has the scheduler and can say what sleeping actually means.

## Problems

Three, in `tests/ch12/locking.c`. The first is the only one in this book that is graded by running
it under real concurrency, because a lock is the one thing that cannot be checked by reading it.

**10.1 — Write a correct lock.**
Four threads take it eight hundred thousand times between them, incrementing an ordinary
non-atomic counter inside. If the lock works the total is exact; the empty stub loses about
seventy per cent of them.

You have `<stdatomic.h>` and not `pthread_mutex`. Two things to get right, and only the first is
about exclusion: taking the lock must be one indivisible operation, and the ordering must be such
that work done inside is visible to the next thread in. A correct exchange with the wrong memory
order passes on a strongly ordered machine and protects nothing on a weak one.

```bash
python3 -m pytest tests/ch12/test_problem_1_lock.py
```

**10.2 — Which reorderings does each barrier actually prevent?**
Eighteen cases. The four that matter are the ones where the annotation is on the operation it does
not help — an acquire on the second access, a release on the first — and the ones where the two
accesses touch the same address, which settles the question before any barrier is consulted.

```bash
python3 -m pytest tests/ch12/test_problem_2_reorder.py
```

**10.3 — Do these two paths disagree about lock order?**
Given the locks each path takes in order, say whether there is a pair taken both ways round.

Deliberately not "will this hang". A conflicting pair is forbidden whether or not you can build a
schedule that hangs today, because tomorrow's schedule is not yours to choose — and two paths can
share every lock they use and be perfectly safe.

```bash
python3 -m pytest tests/ch12/test_problem_3_order.py
```

## Where to go next

The RISC-V unprivileged specification @riscv-isa-unprivileged has the A extension and the memory
model in two separate chapters, which is the right way round: the atomics chapter tells you what
`amoswap` does and the RVWMO chapter tells you what any of it means. Read the `fence` encoding and
notice that `rw,w` is two four-bit fields — the fence you saw is one of two hundred and fifty-six.

xv6's `kernel/spinlock.c` @xv6-riscv-source is sixty lines and now contains nothing you have not
seen the machine code for. The comments around the `__sync_synchronize()` calls say what the fences
are for in the authors' own words, which is a useful second opinion on this chapter's.

[ch13](#ch13) is the other half of what the console driver did. A process that cannot get on
gives up the CPU, and something has to decide what runs instead — which needs a lock, taken across
a context switch, in a way that ought to be impossible.
