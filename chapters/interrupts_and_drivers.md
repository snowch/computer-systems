---
title: "Interrupts and Drivers"
short_title: "19 · Interrupts and Drivers"
---

(interrupts-and-drivers)=
# 19 · Interrupts and Drivers

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch18](#page-faults-as-a-feature) |
| **What it measures** | What a fixed amount of I/O costs in interrupts, for the device where that question has an answer: `bench/results/interrupts-xv6.json` |
:::

## The question

How does a device get the CPU's attention, and what does the CPU do about it?

[ch18](#page-faults-as-a-feature) was about the CPU interrupting itself. A page fault happens *because of* the
instruction that is running: it is caused by that instruction, it is reported at that instruction,
and returning re-runs it. Everything about it is attached to the program it happened to.

A device interrupt has none of those properties. It arrives because something outside the
processor finished doing something, at a moment decided by that thing, while the processor was in
the middle of work with no relationship to it at all. The instruction it lands between is
arbitrary. The process it lands on is very probably not the one that asked.

That difference is why device drivers are shaped the way they are, and this chapter is about
finding out whether you can count the consequences.

## The material

### Getting attention costs someone else's time

The machine has one path in. A device raises a line, the interrupt controller decides which
device is allowed to speak, and the processor takes exactly the trap path [ch16](#traps-and-system-calls) counted —
the same thirty-odd register saves, the same page-table switch, the same restoration on
the way out.

None of that work is the device's. It is charged to whichever process was running, which had
nothing to do with the I/O and is not consulted. A process that performs no I/O at all still pays
for every interrupt that arrives while it holds a core, and it pays in exactly the currency
[ch16](#traps-and-system-calls) measured.

So the obvious question is how many of these there are. That question turns out to have an answer
for one kind of device and not for the other, and finding that out is the useful part of this
chapter.

### A workload that decides its own numbers

```{literalinclude} ../xv6/apps/intrload.c
:language: c
:start-at: int main(void)
:end-before: printf("intrload
```

Build it into the kernel, boot, and run it:

```bash
./run intrload
```

Two devices, deliberately. The console takes characters one at a time; the disk takes blocks. Both
amounts are constants this program chose, so anything that varies between runs is varying for a
reason that is not the workload.

The kernel counts interrupts by source, and counts two extra facts about the console driver:

```{literalinclude} ../xv6/patches/16-interrupt-census.patch
:language: diff
:start-at: +uartnote(int what
:end-before: +// Printed on Ctrl-N
```

### Only one of them is a number

```{figure} _figures/interrupts-and-drivers-sources.svg
:alt: Three interrupt sources, and which of them a fixed workload gives a fixed count for.
:width: 100%

Three sources. Same workload, repeated: one count came back identical every time and two did not.
```

```{include} _generated/interrupts-and-drivers-cost.md
```

The disk count is in the table. The console count is not, and its absence is the finding rather
than an omission.

So is a second absence, arrived at later and the harder of the two. The table used to carry a row
for how many characters the writing process handed to the device itself, which reads like a
companion to the row above it and is not one: the counter behind it is incremented for every
character *the kernel* sends, so it counts the boot log, the shell's prompt and the echo of what
was typed as well as the workload's output. It reported more characters than the workload had
asked for, which is what gave it away, and it came back one different between identical runs often
enough to fail the check that re-runs this measurement. The same argument that keeps the console's
interrupt count out of the table keeps that row out of it.

Run the identical workload five times and the disk raises the same number of interrupts every
time. Run it five times and the console raises a different number every time. Nothing about the
workload changed between those runs, so the console's count is not telling you about the workload.

The reason is in what the two devices are saying. **A block device interrupts to say that a
request is finished.** Requests are discrete, the workload decides how many there are, and each is
completed exactly once — so the count follows. **A character device interrupts to say it is ready
for more.** That is not a unit of anything. How many times a transmitter announces its readiness
during a burst of output depends on how the output and the announcements interleave, which depends
on timing, and timing inside an emulator is a property of the laptop.

This is [ch16](#traps-and-system-calls)'s rule arriving from a new direction. There the uncountable thing was the
timer, and the reason was obviously about elapsed time. Here two devices are doing what looks like
the same job, and only one of them is countable — which is a much better demonstration that the
question is about what an event *means* and not about which peripheral raised it.

### The zero

The most interesting number in the table is the one that is zero.

xv6's console driver is written to be asynchronous. A process writing to the console hands a
character to the transmitter if it is idle, and otherwise **sleeps**, to be woken by the interrupt
that says the transmitter has caught up. That machinery — the sleep, the wait channel, the wakeup
in the handler — is the reason the driver is split into a part that runs in the process and a part
that runs in the interrupt, and it is the standard explanation for why device drivers have two
halves.

In this run it never once engaged. Every character was handed over by the writing process itself,
and the count of times anybody had to stop and wait is zero.

That is not a fault in the driver or in the measurement. It is the emulator: QEMU's transmitter is
always ready, because there is no serial line and nothing is being clocked out at a fixed rate.
The design exists to cope with a device that is slower than the program, and this target does not
have one.

**So this chapter can show you the structure and cannot show you the reason for it.** The split
into two halves is visible in the code, the interrupt that would do the waking is counted, and the
thing that makes any of it necessary — a device that makes a program wait — is absent from the
machine the chapter runs on. [ch29](#the-os-layers-cost) is on hardware where it is not.

### What the image has to do with it

One more dependency, because it caught this chapter out and would otherwise catch a reader out.

The disk figure is reproducible, but it is reproducible *for a filesystem image*. It counts the
block operations xv6's filesystem performs, and how many those are depends on where the blocks
are — which depends on what `mkfs` laid down, which depends on which programs this book has added
to xv6. Add another one in a later chapter and the number moves, for a reason that has nothing to
do with interrupts.

Nothing in the book's stamping scheme covers the filesystem image, because until now nothing had
needed it to. The result records the image's digest so the dependency is visible, and CI
regenerates the measurement on every push, so a change is reported rather than absorbed.

## What we measured

Interrupts raised by the disk for a fixed number of block operations, and what the console driver
did with a fixed number of characters. The two counts the census prints and this book does not
record are named in the result itself rather than quietly dropped, and problem 19.3 asks the reader
to work out which they are before being told.

## What this cannot tell you

**What an interrupt costs.** No duration appears above. The cost of an interrupt is the trap path
plus the handler plus whatever the interruption does to the caches and the pipeline of the
innocent process that was running — and this target models none of the last part. [ch29](#the-os-layers-cost)
prices it.

**How often the timer really fires.** The census counts timer interrupts and the book does not
print the number, for [ch16](#traps-and-system-calls)'s reason. It is worth knowing that this count is *steady* here
over repeated runs and still must not be published: steady on one machine for one short workload
is not the same as determined by the workload, and the difference is exactly the mistake this book
is trying not to make.

**Why the driver is split in two.** The structure is here and the pressure that produced it is
not, because the emulated transmitter is never busy. A reader who wants to see the asynchronous
path do something has to run this on hardware, which is [Part V](#part5).

**Anything about interrupt latency, priority or affinity.** The PLIC can be told which core should
take which interrupt and at what priority; xv6 uses almost none of that, and none of it shows up in
a count. On a machine where a device interrupt can land on the core running your benchmark, those
settings are the difference between a measurement and a puzzle, and [ch30](#whole-machine-profiling) has to care.

## Problems

Three. The first two are in `tests/interrupts_and_drivers/console.c`; the third is a Python stub you fill in with an
opinion and are graded against the machine.

**19.1 — How many characters does the console lose?**
Given a string of arrivals and drains, and a buffer of xv6's own size, say how many are dropped.

A handler cannot block, cannot allocate and has nobody to return an error to, so a character
arriving at a full buffer is simply gone and nothing anywhere is told. This is why a terminal
loses characters when you paste into it, and it is not a bug in anything.

```bash
python3 -m pytest tests/interrupts_and_drivers/test_problem_1_lost.py
```

**19.2 — How many interrupts will this cost?**
Given a number of operations and how many the device reports at once, predict the count — and
return "undecidable" for the device where the workload does not determine it.

The last case is the only one that matters. Being able to say *this question has no answer* is
worth more than any number, and it is a skill this book keeps asking for.

```bash
python3 -m pytest tests/interrupts_and_drivers/test_problem_2_interrupts.py
```

**19.3 — Which of these counts is a property of the workload?**
Six counters; mark each reproducible or not, before running anything.

You are not being graded against what this book decided. The test boots xv6 several times and
compares the censuses, so a counter you called reproducible had better come back the same every
time. Where the experiment cannot settle one — a varying counter that happened not to vary — you
are told so rather than failed, because a test that occasionally fails a correct answer is worse
than one that occasionally proves less than it hoped to.

```bash
python3 -m pytest tests/interrupts_and_drivers/test_problem_3_attribute.py
```

## Where to go next

The RISC-V privileged specification @riscv-isa-privileged defines the interrupt causes and the
rules about when a hart will take one; the PLIC's own specification defines claiming and
completing, which is the handshake `devintr` performs twice per interrupt.

xv6's `kernel/uart.c` and `kernel/plic.c` @xv6-riscv-source are both short enough to read at a
sitting. Read `uartwrite` beside `uartintr` and find the sleep and the wakeup that this chapter
measured zero of — the code is written for a device that makes you wait, and seeing it never wait
is the most useful thing this target can show you about it.

[ch20](#locks-and-memory-ordering) is about the problem this chapter has been carefully stepping around. A handler and
a process share a buffer; one of them can start at any instruction of the other; and the counters
in this chapter's own patch are deliberately unlocked, which is a decision that needs defending.
