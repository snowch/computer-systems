---
title: "Traps and System Calls"
short_title: "ch06 Traps and System Calls"
---

(ch06)=
# ch06 · Traps and System Calls

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch05](#ch05) |
| **What it measures** | The length of the trap path, and what a fixed workload asks the kernel for: `bench/results/traps-xv6.json` |
:::

## The question

What does the hardware do when a program asks the kernel for something?

Part I ended with a program loaded into an address space and running. It cannot do anything
useful on its own — it cannot read a file, write to the console, or obtain more memory — because
none of those are things a user program is permitted to do. Everything interesting requires asking,
and the asking has a mechanism. This chapter is that mechanism, end to end, for one call.

## The material

### A trap is not a call

The instruction is `ecall`, and the temptation is to read it as a function call into the kernel.
It is not, and nearly every way the two differ matters.

A function call is an agreement. The caller knows it is calling, has arranged its registers
accordingly, and the convention tells both sides who preserves what — that was [ch04](#ch04).
**An interrupt is not an agreement.** The interrupted code did not ask, made no arrangements, and
must find every register exactly as it left it. There is no calling convention to lean on, because
one side of it never agreed to anything.

So the trap path cannot save "the callee-saved registers". It has to save **everything**, and put
everything back.

### The hardware's half

`ecall` does a small, fixed amount of work, and the smallness is the point — this is the part
implemented in silicon @riscv-isa-privileged. It records the address of the instruction that
trapped, records why the trap happened, disables interrupts, switches the privilege level, and
jumps to an address the kernel installed earlier.

It does *not* save registers, switch stacks, or change the page table. The processor's contribution
is to get control to a known address with the reason available, and everything else is software's
problem. That division is worth holding on to, because it is the same on every architecture even
where the names differ.

### The software's half, and the page it lives in

```{figure} _figures/ch06-trap-path.svg
:alt: One system call from ecall to sret, with the state movement at each end.
:width: 100%

The work you asked for is the box in the middle.
```

There is a problem the diagram does not show and the code has to solve. The kernel runs with a
different page table from the process, so at some point the address space must change — and the
instant it changes, the code that is running must still be mapped, or the next instruction fetch
faults. A page table cannot be swapped from code that is only in one of the two.

xv6 solves it the way real kernels do: one page, the **trampoline**, mapped at the same virtual
address in every address space, kernel and user alike. The switch happens inside that page, so
whichever table is active the instruction after the switch is at an address that is still valid.
[ch07](#ch07) is where page tables become a mechanism rather than a word; this is the one place in
Part II where a chapter has to promise that something later will make sense.

### How long is the path?

```{include} _generated/ch06-path-counts.md
```

That is the whole of the state movement: the way in saves thirty-one registers, the way out
restores them, and neither is doing anything you asked for. Before `usertrap` has looked at why it
was entered — before any argument has been examined or any work begun — the machine has executed
over eighty instructions of pure bookkeeping.

`uservec` also does a handful of CSR operations, and one of them is the page-table switch.
`userret` does fewer, because part of the return is `sret` itself putting the privilege level and
the interrupt state back in one instruction.

**This is a count and not a cost**, and the distinction is the whole reason it appears here rather
than in Part III. What an instruction costs depends on a pipeline and a cache, and this target has
neither. What is true regardless of the machine is that the path is this long. [ch19](#ch19) takes
the same shape to hardware and puts a price on it.

### Counting what actually happens

The kernel has been patched to count every trap by cause and print the table when you press
Ctrl-T, the way it already prints the process table on Ctrl-P:

```{literalinclude} ../xv6/patches/06-trap-census.patch
:language: diff
:start-at: +static void
:end-before: +// Printed on Ctrl-T
```

Run a fixed workload and ask:

```{include} _generated/ch06-census.md
```

Two things in that table are worth a paragraph each.

**Almost nine hundred system calls to list a directory and echo a line.** Not because the shell is
wasteful — because a system call is the unit in which a program talks to the world, and reading a
directory means opening it, reading it in pieces, and closing it, while printing means writing.
The number is large because the granularity is fine.

**The interrupt counts are deliberately absent**, and the absence is a measurement decision rather
than an omission. An exception is caused by an instruction your program executed: run the same
program again and the same instructions trap the same number of times. An interrupt is caused by a
device or a timer deciding to interrupt, which depends on *how long things took* — and how long
things take inside QEMU is a property of the laptop it is running on. Recorded as a number it
would move on every run and every machine while looking exactly like the number above it.

So the causes are recorded and the counts are not. This is the discipline of [ch00](#ch00) applied
to a case where it costs something: a figure that would have been easy to print, left out because
it would not have meant anything.

### The register census, and why it is not thirty-two

Thirty-one registers are saved. RV64 has thirty-two. The missing one is not an oversight and
working out which it is — and why a trap path is allowed to ignore it — is one of this chapter's
problems.

## What we measured

A path length, read out of the built kernel, and a trap census, read out of a running one. Neither
is a duration and this target could not produce one honestly.

The census is reproducible because the workload is fixed and because only the deterministic half
of it is recorded. CI re-runs it on every push and compares, which is a real check: a kernel patch
that accidentally changed how many system calls the shell makes would move that number, and moving
it silently is exactly the failure the whole stamping scheme exists to prevent.

## What this cannot tell you

**What any of this costs.** The path is eighty-odd instructions long; whether that is expensive
depends on whether they hit in cache, whether the pipeline drains, and what the page-table switch
does to the TLB — three questions this target has no opinion about whatsoever. It is entirely
possible for the *shorter* of two paths to be the slower one, and [ch19](#ch19) is where that gets
settled.

**What a real kernel's path looks like.** xv6's is short because xv6 is small. Linux's does
considerably more on the way in — checking for signals, handling seccomp filters, auditing — and
its fast paths exist precisely to avoid some of it. The shape is the same; the length is not.

**Why the timer fires when it does.** The census shows timer interrupts occurred and nothing else
about them, because their frequency here is an artefact of emulation. [ch11](#ch11) explains what
the kernel does with them.

**Anything about interrupts arriving during a trap.** `ecall` disables them and `usertrap` turns
them back on deliberately, at a point chosen for a reason the code comments explain. Nested traps,
and what happens when one arrives at the wrong moment, are [ch09](#ch09)'s subject.

## Problems

Two, and the first is the one every xv6 reader should do once.

**6.1 — Add a system call, end to end.**
The census is printed on Ctrl-T, which is no use to a program. Add `trapcount()` and a user program
that calls it.

Five files have to agree before this works, and finding all five is the exercise: the number that
identifies the call, the table that dispatches on it, the declaration the user program compiles
against, the stub that issues `ecall`, and the kernel function itself. Leaving any one out produces
an error that does not mention the others.

The test cannot check that your number is *correct* without reimplementing your counter, so it
checks the two things that separate a working system call from a plausible stub: the value is not
zero, and it grows between two runs. A constant fails both.

```bash
python3 -m pytest tests/ch06/test_problem_1_addcall.py
```

**6.2 — Which registers must be saved, and which need not be?**
Count them, then say which ones `uservec` leaves alone and why each is allowed. There is more than
one reason a register can end up on that list, and this chapter has given you two of them.

The test reads the count out of the kernel as built, so if you patch the trampoline you are graded
against your own kernel rather than against the book's.

```bash
python3 -m pytest tests/ch06/test_problem_2_registers.py
```

## Where to go next

The RISC-V privileged specification @riscv-isa-privileged defines exactly what `ecall` and `sret`
do and what each CSR in the path is for. The section on trap handling is short, and reading it
alongside `trampoline.S` is the fastest way to work out which half of the path is hardware.

xv6's `kernel/trampoline.S` and `kernel/trap.c` @xv6-riscv-source are now readable in full — the
assembly is the path this chapter counted, and `usertrap` is forty lines of C. Read the assembly
first and the C second; the order matters, because the C makes no sense until you know what state
it has been handed.

[ch07](#ch07) takes the promise this chapter made — that a page table is a thing, that the
trampoline is mapped into two of them — and turns it into something you can print.
