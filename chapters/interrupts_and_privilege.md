---
title: "Interrupts, and Who Is Allowed To"
short_title: "05 · Interrupts, and Who Is Allowed To"
---

(interrupts-and-privilege)=
# 05 · Interrupts, and Who Is Allowed To

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [ch04](#a-trap-with-nothing-else) |
| **What it measures** | A timer interrupt taken with no kernel present, and an access refused because the program had dropped a privilege level. |
:::

## The question

What arrives without being asked for, and what does a privilege level actually restrict?

[ch04](#a-trap-with-nothing-else)'s trap was caused. An instruction executed, and the trap was that
instruction's consequence — remove the `ecall` and nothing happens. This chapter is about the other
kind, which no instruction causes and which would arrive if the program were doing nothing at all.
And about the machinery that makes the word "allowed" mean something, which turns out to be a
two-bit field and a refusal.

## The material

### Something that arrives on its own

The timer is a device that counts. `mtime` goes up whether or not anybody reads it; when it reaches
`mtimecmp`, the processor takes an interrupt. Both live at fixed addresses on this board, and there
is nothing else to it:

```{literalinclude} ../sysfs/bare/privilege.c
:language: c
:start-at: #define CLINT_BASE
:end-before: #define MSTATUS_MIE
```

Arming it takes three writes — one to say *when*, one to enable this particular interrupt, and one
to enable interrupts at all. The two-level enable is not redundancy: the per-source bit says which
interrupts a program is interested in, and the global bit is what a critical section turns off.

```{literalinclude} ../sysfs/bare/privilege.c
:language: c
:start-at: static void wait_for_the_timer(void)
:end-before:     bare_csr_clear(mstatus, MSTATUS_MIE);
```

The loop asks for nothing. It reads no device, executes no `ecall`, touches no memory it does not
own, and left alone it would run until the machine was switched off. The interrupt is what stops
it, and that is the whole difference from the previous chapter.

### Two kinds of cause, one register

`mcause` reports both kinds, and the top bit is which. That bit is also the reason the handler can
be one function:

```{literalinclude} ../sysfs/bare/privilege.c
:language: c
:start-at:     if (cause & CAUSE_INTERRUPT)
:end-before:     if (phase == PHASE_SUPERVISOR)
```

Note what is missing: the `mepc + 4` from ch04. An interrupt's `mepc` is wherever the program
happened to be — no instruction caused it, so there is nothing to advance past, and advancing
would skip an instruction that had not run yet. The same register, read two different ways,
depending on one bit.

### What a privilege level refuses

Machine mode may do anything. Supervisor mode may not, and this is the smallest demonstration of
what "may not" means in hardware:

```{literalinclude} ../sysfs/bare/privilege.c
:language: c
:start-at: /* Supervisor mode tries to read a machine-mode register.
:end-before: __attribute__((interrupt("machine"), aligned(4))) static void handler
```

One instruction, reading one register. In machine mode it succeeds; in supervisor mode the
processor refuses, and the refusal is itself a trap — cause 2, illegal instruction. There is no
error code, no signal and no return value. The instruction simply does not happen and control
leaves for the handler.

Getting into supervisor mode is the same instruction that returns from a trap. `mret` goes to
`mepc` at the privilege level named in `mstatus.MPP`, so setting that field to *supervisor* and
executing `mret` is a deliberate demotion:

```{literalinclude} ../sysfs/bare/privilege.c
:language: c
:start-at: static void be_refused(void)
:end-before: int main(void)
```

`bare_open_memory()` is there for a reason worth knowing before it costs you an afternoon. With no
firmware in front of the program every physical-memory-protection region starts closed, and closed
means closed to supervisor and user mode — machine mode is exempt. Without it, the supervisor
program faults on its first instruction, with a cause that has nothing to do with what it was
trying to do.

### And getting back

Only through a trap. The handler notices which phase the program is in, puts *machine* in `MPP`,
and points `mepc` at the address the program recorded before it left:

```{literalinclude} ../sysfs/bare/privilege.c
:language: c
:start-at:     if (phase == PHASE_SUPERVISOR)
:end-before:     /* An exception nobody planned for.
```

`mret` restores no registers at all, which is the detail that makes this genuinely awkward and
which `bare_enter_supervisor()` exists to handle once rather than three times. [ch09](#fork-built-rather-than-read)
is where that stops being an inconvenience and becomes the subject.

## What we measured

Run it yourself before reading the table — the numbers below are what you should
see, and a figure you have reproduced is worth more than one you have been shown:

```bash
./run privilege
```

```{include} _generated/interrupts-and-privilege-privilege.md
```

## What this cannot tell you

**What an interrupt costs, or how long it takes to arrive.** Not measurable here and not
measurable under any emulator: interrupt latency is a property of a pipeline, and QEMU has none.
[ch27](#the-os-layers-cost) asks that question on hardware.

**How real interrupt sources behave.** One timer is the simplest possible case: one source, no
routing, no priority, no sharing. A real machine has an interrupt controller deciding which device
may interrupt which core, which is [ch17](#interrupts-and-drivers) — and the controller is exactly
the part this chapter leaves out.

**What the other privilege level does.** There is a user mode below supervisor, and this chapter
never enters it. Nothing here needed it, and a demonstration with a level that made no difference
would have taught that levels make no difference.

## Problems

**5.1 — Interrupt an interrupt.**
Arrange for the timer to fire while the handler is still running, and say what happens and why.
Then make it happen. The test checks both your prediction and a run, and the interesting part is
that the default answer is *nothing*, for a reason in one bit of `mstatus`.

```bash
python3 -m pytest tests/interrupts_and_privilege/test_problem_1_nested.py
```

**5.2 — Advance `mepc` on an interrupt.**
Make the handler treat the interrupt as ch04 treated the trap, and add four. Say exactly what goes
wrong and produce a run where the damage is visible in the output rather than inferred.

```bash
python3 -m pytest tests/interrupts_and_privilege/test_problem_2_wrong_epc.py
```

**5.3 — Find another refusal.**
`csrr t0, mhartid` is one instruction supervisor mode may not execute. Find a second, of a
different kind — not another machine-mode register — and demonstrate it, reporting its cause. The
test checks the cause differs from 2 and that your program really did run in supervisor mode.

```bash
python3 -m pytest tests/interrupts_and_privilege/test_problem_3_another_refusal.py
```

## Where to go next

The privileged specification @riscv-isa-privileged defines the cause codes, `mstatus.MPP` and the interrupt
enable bits. Its table of causes is one page and worth reading in full once: most of the entries
are things you can arrange to see from a program this size.

[ch06](#one-page-table-two-harts) adds the other thing that arrives without being asked for, which
is a second processor.
