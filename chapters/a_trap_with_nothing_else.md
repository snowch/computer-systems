---
title: "06 · A Trap, With Nothing Else in the Machine"
short_title: "06 · A Trap, With Nothing Else in the Machine"
---

(a-trap-with-nothing-else)=
# 06 · A Trap, With Nothing Else in the Machine

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `bare` — a RISC-V machine in QEMU without an operating system |
| **Prerequisites** | [Part II](#part2), [ch05](#c-for-people-who-will-read-a-kernel) |
| **Evidence** | The handler address, saved instruction address and return from one deliberate trap. |
:::

## The question

What is a trap, when nothing else is going on?

A trap transfers control to a handler when an instruction raises an exception or an interrupt
arrives. This example deliberately executes a trap instruction and runs its handler on a RISC-V
machine in QEMU. Follow where the processor saves the instruction address and how the
handler resumes the program.

(a-trap-with-nothing-else-example)=
## Follow one trap and return

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

This example installs one machine-mode handler. The handler reads `mcause` to find why the
trap occurred. [ch07](#interrupts-and-privilege) compares causes from an interrupt and an
exception.

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

`ecall` occupies four bytes @riscv-isa-unprivileged, so the handler adds four to resume at the
next instruction in this example. [ch02](#reading-a-listing) shows RISC-V builds with shorter
compressed instructions. A handler that skips a trapping instruction has to account for that
instruction’s length and the reason for the trap.

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

From your repository root, run the original example. The script builds `sysfs/bare/trap.c` and
starts it in QEMU without an operating system.

```bash
./run trap
```

Find `mepc_is_the_ecall`, `mepc_advance`, `resumed` and `taken` in the terminal output. The
boolean fields use `1` for true. Which fields show where the processor recorded the trap and
which show that it returned after a single trap? Compare them with the book’s recorded run.

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

Use the files below in your local checkout. Run each test command from the repository root.

**6.1 — Why four, and when is it not?**
Open `tests/a_trap_with_nothing_else/problem_1_advance.py`. Fill in the meaning of the offset
added to `mepc`, an instruction for which that offset would be wrong, and the instruction’s
byte length. The test assembles your instruction and checks the length.

```bash
python3 -m pytest tests/a_trap_with_nothing_else/test_problem_1_advance.py
```

**6.2 — Make it loop, then explain it.**
Open `tests/a_trap_with_nothing_else/problem_2_forever.py`. Copy `sysfs/bare/trap.c` to `tests/a_trap_with_nothing_else/answer_forever.c`. In your copy,
remove `bare_csr_write(mepc, seen_epc + 4);`. In the Python stub, name the instruction that repeats and explain why the
processor keeps executing it. The test boots your copy and expects a timeout. That timeout is
the observation for this problem.

```bash
python3 -m pytest tests/a_trap_with_nothing_else/test_problem_2_forever.py
```

**6.3 — Take the compiler's help away.**
Copy `sysfs/bare/trap.c` to `tests/a_trap_with_nothing_else/answer.c`. Implement the handler
in the copy without the `interrupt("machine")` attribute. The test checks for `mret` and for
`register_survived` with value `1` in the console output.

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
