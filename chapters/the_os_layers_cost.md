---
title: "The OS Layer's Cost on Real Hardware"
short_title: "27 · The OS Layer's Cost on Real Hardware"
---

(the-os-layers-cost)=
# 27 · The OS Layer's Cost on Real Hardware

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Answers the cost of** | [ch14](#traps-and-system-calls), [ch16](#page-faults-as-a-feature), [ch19](#scheduling-and-context-switches) |
| **Prerequisites** | [ch26](#memory-ordering-on-real-hardware) |
| **What it measures** | The trap instruction and the call that hides it: `bench/results/oscalls-aarch64.json` |
:::

## The question

What does Linux charge for the services xv6 showed me?

Part IV took three things apart — a system call, a page fault, a context switch — and counted
what each one moved. It could not do anything else: the target has no cache, no predictor and no
memory latency, so a duration measured there describes a laptop. This is the chapter where those
three things meet a machine with a clock, and the counts become a model that can be wrong.

## The material

### What Part IV left

```{include} _generated/the-os-layers-cost-model.md
```

Every figure in that table was counted rather than timed, and each is still true — an instruction
count is a property of the kernel as built, not of the machine that ran it. What they are not is
a cost. They are a *floor*: the work has to happen, so the call cannot be cheaper than executing
it, and problem 19.2 turns the count into that bound.

A bound is worth having because of what it does when the measurement arrives. Come in under it
and the model is wrong — some of those instructions are not on the path, or are not being
executed. Come in a little over it and the model explains the cost. Come in far over it and the
model was never the expensive part, and the interesting question becomes what the rest is.

### A trap, and the call that hides it

Here is a system call written as the instruction it is.

```{include} _generated/the-os-layers-cost-trap.md
```

Three ideas and nothing else: put the call number where the kernel's convention says to put it,
execute the instruction that changes privilege level, come back. There is no stack frame, because
by [ch12](#machine-level-code-on-riscv)'s rule a function that calls nothing needs none — and this function does not
call anything. It traps.

Note which convention that is. The register holding the call number is not one the C calling
convention would have chosen, and it could not be: the process and the kernel were compiled
separately, by different people, at different times, so they cannot have agreed by being compiled
together. They agree by specification instead, which is the reason a system call is not a
function and cannot be made into one.

Now the same request, written the way anybody would write it.

```{include} _generated/the-os-layers-cost-call.md
```

A frame, a branch, and a sign-extension to widen what the kernel returned. The trap is not in
this listing at all. It is somewhere past that branch, in code shipped with the machine, and
nothing at the call site distinguishes it from a call that never leaves the process.

**That is the chapter's difficulty stated in one figure.** Cost in this layer is not visible in
the code. Two calls that look identical in C can differ by whether a privilege boundary is
crossed, and the compiler will not tell you, because the compiler does not know either.

### The instrument and the thing

[ch22](#measuring) built the clock and, more usefully, measured what reading it costs. This is the
chapter where that second number decides whether a measurement means anything.

The trap is small. If the thing being timed is of the same order as the instrument, a harness
that reads the clock on both sides of every call is charging the instrument to every call, and no
number of iterations divides it away — it is added, not amortised. Read the clock once before the
loop and once after, and the same overhead is divided by however many iterations there were.

Problem 19.1 is that arithmetic, and it is arithmetic rather than a rule for a reason: at a single
iteration the two arrangements give the same answer. Putting the clock outside the loop does not
remove the overhead. It divides it, and dividing by one is not a saving.

The cost of this mistake is not a slightly wrong number. It is a confident, stable, reproducible
measurement of `clock_gettime`, which will look exactly like a measurement of whatever was in the
loop and will not change when the loop's contents do.

### What the three cost

```{include} _generated/the-os-layers-cost-cost.md
```

Every row has a baseline beside it, because a duration on its own is not a cost. Knowing what a
system call takes is not useful until it is beside the cheapest thing the machine can do, and it
is the ratio that survives being read on a different machine two years from now.

The baselines are chosen to be unflattering. A system call compared against an empty function
call; a fault compared against a write to a page that is already there; a context switch compared
against the same work done without leaving the thread. In each case the comparison is between
doing the thing and not doing it, which is the only comparison that answers "what did the kernel
cost me".

### Two faults that are not the same fault

```{include} _generated/the-os-layers-cost-faults.md
```

[ch16](#page-faults-as-a-feature) counted faults and made the case that a fault is a feature — the mechanism by which
a page arrives only when it is wanted. It counted them because that target could not price them,
and it could not price them because the interesting difference between two faults is where the
data came from, and QEMU's storage is a host file.

Both faults in that table enter the kernel by exactly the path [ch14](#traps-and-system-calls) traced, and leave it
the same way. Nothing about the trap differs. What differs is whether the kernel could answer
from memory it already had or had to go and ask storage, and problem 19.3 is the classification:
four facts about an address, and the order the rules apply in.

The order is most of the content. A page the process never asked for is fatal however good it
looks; a translation that already exists costs nothing whatever else is true; and only then does
the minor-against-major question arise at all.

### The call that does not trap

```{include} _generated/the-os-layers-cost-vdso.md
```

Some system calls are not system calls. The kernel maps a page of its own code into every
process, and a few requests — reading the clock is the one that matters here — are served by
running that code with no privilege change at all. The answer comes from memory the kernel keeps
up to date, and the process never traps.

This closes a loop opened five chapters earlier. [ch22](#measuring)'s clock is cheap enough to time
things with *because* of this mechanism; a clock that trapped would be an instrument of the same
order as much of what Part V measures, and most of this book's timings would be impossible to
take in the form they are taken.

And it is the listing above, made expensive. Two calls, indistinguishable in C, one of which
crosses a privilege boundary and one of which does not. You cannot read that off the page. You
can only measure it.

## What we measured

The trap instruction and the call that hides it, compiled for the reference architecture. That
listing needs no board — an instruction sequence is a property of the compiler — and it is the
one figure here that CI regenerates and diffs on every push.

Everything with a duration in it is pending, and waits on the machine: what the three services
cost against their baselines, what separates a minor fault from a major one, and what the vDSO
saves. The counts they will be compared against are already in the book, taken in Part IV, which
is the point of having spent Part IV counting.

## What this cannot tell you

**What a system call costs.** It cannot, and no measurement can. `getpid` is chosen precisely
because the kernel does almost nothing after the trap, so what the table reports is the floor —
the cost of the boundary itself. A `read` that returns a megabyte is mostly not boundary cost, and
dividing this chapter's figure into it would explain none of it.

**What it costs your program.** These calls are made in a loop, with the caches and the TLB warm
and the branch predictor already trained on the path. A call made once, in the middle of other
work, also evicts what that work had cached, and the eviction is charged to the code that runs
next rather than to the call. Finding that in a real program is [ch28](#whole-machine-profiling)'s equipment.

**Anything about a differently configured kernel.** The same source, built with different
hardening options or booted with different mitigations, is a different measurement. This book
takes one, on one kernel, and records which — it does not survey them, and a reader who needs the
comparison has to take it themselves.

**What xv6 charges.** Part IV's counts stay counts. There is no version of this chapter that
prices the kernel the reader can stop mid-trap, because the machine it runs on is a program, and
that is the trade the two targets were chosen to make.

**Whether the model explains the cost.** The bound in problem 19.2 says what the call cannot beat.
If the measurement is far above it, this chapter has established that Part IV's account is
incomplete without establishing what is missing — and the instruction count is not where the
answer will be found.

## Problems

Three, in `tests/the_os_layers_cost/oscost.c`.

**27.1 — Where does the clock go?**
Two harnesses, identical except for where they read the clock, and what each reports. Do this
before writing any timing code in the chapters that follow.

```bash
python3 -m pytest tests/the_os_layers_cost/test_problem_1_instrument.py
```

**27.2 — What can it not be cheaper than?**
Turn [ch14](#traps-and-system-calls)'s instruction count into a floor, given an IPC and a clock. Divide once at the
end: a bound that has been rounded twice is an estimate.

```bash
python3 -m pytest tests/the_os_layers_cost/test_problem_2_bound.py
```

**27.3 — Which fault is this?**
Four facts about an address and a stated precedence. The minor-against-major split is the one
worth orders of magnitude, and it is not a fact about the fault.

```bash
python3 -m pytest tests/the_os_layers_cost/test_problem_3_faults.py
```

## Where to go next

The AArch64 exception model is specified in the ARM architecture reference manual, and reading
its description of what `svc` does beside [ch14](#traps-and-system-calls)'s account of `ecall` is the fastest way to
see which parts of a trap are architecture and which are xv6. The system-call numbering the
listing above uses is Linux's own, in `include/uapi/asm-generic/unistd.h` in the kernel tree.

[ch28](#whole-machine-profiling) stops assuming you know which code to look at. Everything measured so far has been
code this book wrote, in a loop chosen to isolate one mechanism; the next chapter is about finding
the expensive part of a program nobody here has read.
