---
title: "A Trap, With Nothing Else in the Machine"
short_title: "06 · A Trap, With Nothing Else in the Machine"
---

(a-trap-with-nothing-else)=
# 06 · A Trap, With Nothing Else in the Machine

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [Part II](#part2), [ch05](#c-for-people-who-will-read-a-kernel) |
| **What it measures** | The whole of a trap in one program: where the handler was, where the interrupted instruction was, and that execution resumed after it. |
:::

## The question

What is a trap, when nothing else is going on?

A trap is a jump the processor makes without being asked, to an address it was given in
advance. [Part II](#part2) said why a kernel is a hard place to learn that: almost nothing on the
page is the mechanism. Here there is nothing else — no kernel, no library, no loader, and no
operating system. One handler, one deliberate trap, and every question about it answered by the
machine.

## The material

### The whole machine

Three files, and between them they are the entire runtime. The linker script says where the
program goes, because with `-bios none` — no firmware — QEMU releases the processor at a fixed
address and expects to find instructions there.

```{literalinclude} ../sysfs/bare/bare.ld
:language: text
:start-at: SECTIONS
:end-before: .rodata
```

The entry code makes a stack and zeroes the memory C is entitled to assume is zero — every
variable outside a function that was declared without a value. Nothing else will: there is no
loader to set memory up, and no runtime to call before `main`.

```{literalinclude} ../sysfs/bare/start.S
:language: asm
:start-at: _entry:
:end-before: bnez    t0, wait_for_hart0
```

And the console is two device registers. Writing a byte to one sends it; the other says whether
the device is ready for the next. That is the whole driver. The kernel's version in
[ch19](#interrupts-and-drivers) is these same two registers underneath a great deal of machinery
about sleeping and waking.

```{literalinclude} ../sysfs/bare/console.c
:language: c
:start-at: void bare_putc(char c)
:end-before: void bare_print
```

### Where the processor goes

One register decides where a trap lands: `mtvec`, the machine trap vector, holds the address to
go to. It is one of the processor's *control and status registers* — CSRs, a set apart from `a0`
and its neighbours, read and written with instructions of their own, which is what
`bare_csr_write` wraps. The `m` is for *machine mode*, the most privileged state the processor
has and the one it comes out of reset in; [ch07](#interrupts-and-privilege) is where the other
modes appear.

```{literalinclude} ../sysfs/bare/trap.c
:language: c
:start-at:     bare_csr_write(mtvec, (uint64)handler);
:end-before:     /* s2 is set before the trap
```

Build it and boot it on a machine with nothing on it:

```bash
./run trap
```

That is the installation, complete. There is no table of handlers, no registration, and nothing to
tell the processor which kinds of trap this handler wants — it gets all of them. Sorting out which
is which is the handler's job, and it reads `mcause` to do it —
[ch07](#interrupts-and-privilege)'s subject.

### Where it was, and the mistake that loops for ever

The processor also records where it was when the trap happened, in `mepc` — the saved *program
counter*, the processor's record of which instruction it is on. Exactly which instruction that
means is the first thing about traps that surprises people:

```{literalinclude} ../sysfs/bare/trap.c
:language: c
:start-at:     /* mepc holds the address *of* the instruction that trapped
:end-before: }
```

```{figure} _figures/a-trap-with-nothing-else-path.svg
:alt: What the hardware writes at a trap, and what it leaves untouched.
:width: 100%

Three registers and the program counter. Everything a reader associates with a trap — a saved
frame, a process, a dispatch — is software somebody wrote, and none of it is here yet.
```

`mepc` points **at** the instruction that trapped, not past it. A handler that returns without
moving it re-executes the same instruction, which traps again, into the same handler, for ever.
The machine does not consider this an error. It is doing exactly what it was told, and the symptom
is a program that prints nothing and never finishes.

Whether four is the right number to add is not obvious either. [ch02](#reading-a-listing)
pointed out that instructions on this architecture are not all the same length, so adding a fixed
four ought to look reckless. It is safe here only because the programs in this part are built
for `rv64g`, without the compressed extension — the short forms [ch02](#reading-a-listing)
mentioned — so every instruction in them really is four bytes. That is a property of the build,
not of the processor, and the first problem below is about what happens when it stops holding.

### What a trap does not do

It does not save anything. Not the registers, not the stack, not a frame — the processor changes
`mepc`, `mcause` and a couple of bits of `mstatus`, its status register, then jumps, and that is
all. Every register still
holds what the interrupted code put there, and the instant the handler uses one, that value is
gone.

Here the compiler covers for us:

```{literalinclude} ../sysfs/bare/trap.c
:language: c
:start-at: /* `interrupt("machine")` makes the compiler do two things
:end-before:     taken++;
```

What the compiler saves is a private matter between the handler's first instructions and its
last — the `mret` that jumps back to `mepc`: the C in between cannot name those slots, cannot
read what the interrupted code had in `a0`, and cannot change what it will get back. That is fine here, because this handler has
nothing to say to the code it interrupted. A trap that is *told* something and has to *answer* —
a system call, which takes its arguments from the caller's registers and puts its result back
into one — needs the saved registers laid out where the handler can reach them, and that is a
frame written by hand. It is [ch09](#a-system-call-of-your-own), and it is why that handler
saves all thirty-one itself.

### Proving it

The program sets a register, traps — with `ecall`, the instruction whose only job is to trap —
and reads the register back afterwards. `asm volatile` is how C embeds instructions of your own;
the `volatile` is [ch05](#c-for-people-who-will-read-a-kernel)'s, and stops the compiler
removing them.

```{literalinclude} ../sysfs/bare/trap.c
:language: c
:start-at:     asm volatile("li   s2, 0x5eed\n"
:end-before:     bare_printf("trap mtvec_is_handler
```

## What we measured

Run it yourself before reading the table — the rows below are what you should see, and a
figure you have reproduced is worth more than one you have been shown:

```bash
./run trap
```

```{include} _generated/a-trap-with-nothing-else-trap.md
```

Every row is the machine answering rather than the chapter asserting, and `bench/run_bare.py`
refuses the run if any of them stops being true — including the two that look like formalities:
that `mtvec` reads back what was written, and that the program resumed, which it proves by
reaching the line that prints it. If `mepc_is_the_ecall` ever came back *no*, the paragraph above
about the infinite loop would be describing a different processor.

## What this cannot tell you

**How long a trap takes.** Nothing on this target may be timed, for the reason
[Part I](#part1) gives: a duration measured under QEMU is a fact about the laptop running the
emulator. What a trap *costs* is [ch29](#the-os-layers-cost), on hardware.

**What a real board does before your code runs.** QEMU with `-bios none` hands the processor over
at the reset address with the machine in a defined state. [Part II](#part2) says what a physical
board does instead, and why this program will not boot one unchanged.

**Whether the compiler will keep covering for you.** `interrupt("machine")` saved the registers
because this handler had nothing to hand back. The moment a trap has to answer the code it
interrupted, the saving is yours to write.

## Problems

Three, and the second one is the one that catches people.

**6.1 — Why four, and when is it not?**
The handler adds four to `mepc`. Say what that four actually is, and give a case in this
instruction set where adding four would resume in the wrong place. The test asks for both, and
checks the second against an assembled instruction rather than against a claim.

```bash
python3 -m pytest tests/a_trap_with_nothing_else/test_problem_1_advance.py
```

**6.2 — Make it loop, then explain it.**
Remove the line that advances `mepc` and run the program. Record how the harness reports what
happens, and say precisely which instruction executes how many times. The test checks that your
description matches a run it performs itself, so "it hangs" does not pass.

```bash
python3 -m pytest tests/a_trap_with_nothing_else/test_problem_2_forever.py
```

**6.3 — Take the compiler's help away.**
Rewrite the handler without `interrupt("machine")`, as an ordinary function, and make the program
still print `register_survived yes`. You will need to say what `mret` is and where it has to go.
The test compiles your handler, boots it, and checks both the output and that the attribute is
genuinely absent.

```bash
python3 -m pytest tests/a_trap_with_nothing_else/test_problem_3_by_hand.py
```

## Where to go next

The privileged specification @riscv-isa-privileged is the source for `mtvec`, `mepc`, `mcause` and `mret`,
and is worth opening at the machine-mode trap chapter now rather than later: it is short, and
everything in it is something this program did.

[ch07](#interrupts-and-privilege) adds the thing that arrives without being asked for.
[ch16](#traps-and-system-calls) is this mechanism again with a kernel around it, which is a good
deal easier to read having built the middle of it.
