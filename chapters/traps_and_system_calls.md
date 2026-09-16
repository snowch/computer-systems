---
title: "Traps and System Calls"
short_title: "16 · Traps and System Calls"
---

(traps-and-system-calls)=
# 16 · Traps and System Calls

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch15](#linking-and-loading) |
| **What it measures** | The length of the trap path, and what a fixed workload asks the kernel for: `bench/results/traps-xv6.json` |
:::

## The question

What does the hardware do when a program asks the kernel for something?

[Part III](#part3) ended with a program loaded into an address space and running. It cannot do anything
useful on its own — it cannot read a file, write to the console, or obtain more memory — because
none of those are things a user program is permitted to do. Everything interesting requires asking,
and the asking has a mechanism. This chapter is that mechanism, end to end, for one call.

## The material

### A trap is not a call

The instruction is `ecall`, and the temptation is to read it as a function call into the kernel.
It is not, and nearly every way the two differ matters.

A function call is an agreement. The caller knows it is calling, has arranged its registers
accordingly, and the convention tells both sides who preserves what — that was [ch14](#machine-level-code-on-riscv).

`ecall` is the one trap a program does agree to, and it gets nothing for agreeing, because
**it has no path of its own.** One entry point serves it, a division by zero, a page fault and a
timer interrupt alike, and three of those four arrive without being asked for: the interrupted
code made no arrangements and has to find every register exactly as it left it. A path that must
satisfy the worst of its callers has no calling convention to lean on.

So the trap path cannot save "the callee-saved registers". It has to save **everything**, and put
everything back. The census at the end of this chapter is that claim as a table — one counter,
entered for several unrelated reasons.

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

```{figure} _figures/traps-and-system-calls-trap-path.svg
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
[ch17](#virtual-memory) is where page tables become a mechanism rather than a word; this is the one place in
[Part IV](#part4) where a chapter has to promise that something later will make sense.

### How long is the path?

```{include} _generated/traps-and-system-calls-path-counts.md
```

That is the whole of the state movement: the way in saves thirty-one registers, the way out
restores them, and neither is doing anything you asked for. Before `usertrap` has looked at why it
was entered — before any argument has been examined or any work begun — the machine has executed
over forty instructions of pure bookkeeping, and it will execute nearly as many again on the way
out, after the work is finished.

`uservec` also does a handful of CSR operations, and one of them is the page-table switch.
`userret` does fewer, because part of the return is `sret` itself putting the privilege level and
the interrupt state back in one instruction.

**This is a count and not a cost**, and the distinction is the whole reason it appears here rather
than in [Part V](#part5). What an instruction costs depends on a pipeline and a cache, and this target has
neither. What is true regardless of the machine is that the path is this long. [ch29](#the-os-layers-cost) takes
the same shape to hardware and puts a price on it.

### Counting what actually happens

The kernel has been patched to count every trap by cause and print the table when you press
Ctrl-T, the way it already prints the process table on Ctrl-P:

```{literalinclude} ../xv6/patches/13-trap-census.patch
:language: diff
:start-at: +static void
:end-before: +// Printed on Ctrl-T
```

Then run a workload and ask:

```{include} _generated/traps-and-system-calls-census.md
```

**Most of that table is a list rather than a count, and the reason is worth more than the numbers
would have been.**

The obvious thing to measure was the shell: boot, run `ls`, and report how many system calls it
took. That produced a satisfyingly large number — and a different one each time. How many times
the shell calls `read` depends on how the console delivered its characters, which depends on
timing, and elapsed time inside QEMU is a property of the laptop running it. Two runs of an
identical workload disagreed, which is how this was found out rather than assumed.

An exception is caused by an instruction your program executed, so for a *fixed sequence of
instructions* it is reproducible. The trouble is that "run the shell" is not a fixed sequence of
instructions. So the workload is a program that removes the question:

```{literalinclude} ../xv6/apps/trapload.c
:language: c
:start-at: int main(void)
```

Build it into the kernel, boot, and run it:

```bash
./run trapload
```

Nothing else in the system calls `getpid`, so that row of the census is a number this program
decided and the shell's noise lands elsewhere. It asks a thousand times and the kernel counts a
thousand — which is a much smaller claim than the one that was almost printed, and unlike it, true
on every machine.

That is the discipline of [ch00](#prerequisites-and-setup) meeting a case where it costs something. The large number
was easy, impressive, and meaningless. [ch29](#the-os-layers-cost) counts the lot, on a machine where elapsed
time is a fact about the machine.

### The register census, and why it is not thirty-two

Thirty-one registers are saved. RV64 has thirty-two. The missing one is not an oversight and
working out which it is — and why a trap path is allowed to ignore it — is one of this chapter's
problems.

## What we measured

A path length, read out of the built kernel, and a trap census, read out of a running one. Neither
is a duration and this target could not produce one honestly.

The census is reproducible because the workload is fixed and because only the deterministic half
of it is recorded. CI re-runs it on every push and compares, which is a real check: a kernel patch
that lost some of the workload's thousand calls, or that introduced a cause this list does not
have, would move it, and moving it silently is exactly the failure the whole stamping scheme
exists to prevent.

What the check deliberately cannot catch is a change in how often the *shell* asks the kernel for
anything, because that was never recorded. Giving up that number is what bought the rest of the
table its reproducibility, and the section above is the argument.

## What this cannot tell you

**What any of this costs.** The path is eighty-odd instructions long; whether that is expensive
depends on whether they hit in cache, whether the pipeline drains, and what the page-table switch
does to the TLB — three questions this target has no opinion about whatsoever. It is entirely
possible for the *shorter* of two paths to be the slower one, and [ch29](#the-os-layers-cost) is where that gets
settled.

**What a real kernel's path looks like.** xv6's is short because xv6 is small. Linux's does
considerably more on the way in — checking for signals, handling seccomp filters, auditing — and
its fast paths exist precisely to avoid some of it. The shape is the same; the length is not.

**Why the timer fires when it does.** The census shows timer interrupts occurred and nothing else
about them, because their frequency here is an artefact of emulation. [ch21](#scheduling-and-context-switches) explains what
the kernel does with them.

**Anything about interrupts arriving during a trap.** `ecall` disables them and `usertrap` turns
them back on deliberately, at a point chosen for a reason the code comments explain. Nested traps,
and what happens when one arrives at the wrong moment, are [ch19](#interrupts-and-drivers)'s subject.

## Problems

Two, and the first is the one every xv6 reader should do once.

**16.1 — Add a system call, end to end.**
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
python3 -m pytest tests/traps_and_system_calls/test_problem_1_addcall.py
```

**16.2 — Which registers must be saved, and which need not be?**
Count them, then say which ones `uservec` leaves alone and why each is allowed. There is more than
one reason a register can end up on that list, and this chapter has given you two of them.

The test reads the count out of the kernel as built, so if you patch the trampoline you are graded
against your own kernel rather than against the book's.

```bash
python3 -m pytest tests/traps_and_system_calls/test_problem_2_registers.py
```

## Where to go next

The RISC-V privileged specification @riscv-isa-privileged defines exactly what `ecall` and `sret`
do and what each CSR in the path is for. The section on trap handling is short, and reading it
alongside `trampoline.S` is the fastest way to work out which half of the path is hardware.

xv6's `kernel/trampoline.S` and `kernel/trap.c` @xv6-riscv-source are now readable in full — the
assembly is the path this chapter counted, and `usertrap` is forty lines of C. Read the assembly
first and the C second; the order matters, because the C makes no sense until you know what state
it has been handed.

[ch17](#virtual-memory) takes the promise this chapter made — that a page table is a thing, that the
trampoline is mapped into two of them — and turns it into something you can print.
