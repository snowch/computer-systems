---
title: "Scheduling and Context Switches"
short_title: "21 · Scheduling and Context Switches"
---

(scheduling-and-context-switches)=
# 21 · Scheduling and Context Switches

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch20](#locks-and-memory-ordering) |
| **What it measures** | What a context switch moves, and the one switch count a workload decides: `bench/results/switch-xv6.json` |
:::

## The question

What exactly is saved, and what does it mean to say a thread "runs"?

[ch20](#locks-and-memory-ordering) ended on something that ought to be impossible: a lock held across a context switch.
A process gives up the CPU while holding its own lock, another hart picks it up later, and the
release happens on a different core from the acquire. That is not a bug, it is the design, and
understanding why needs a precise account of what a switch actually moves.

## The material

### A switch is a function call, and that is the whole saving

```{include} _generated/scheduling-and-context-switches-swtch.md
```

Read the first two rows against each other, because the ratio is the point.

[ch16](#traps-and-system-calls)'s trap path saves thirty-one registers. `swtch` saves fourteen. Both are moving "the
state of a thread" and one of them moves less than half as much, which looks like an optimisation
and is not.

**A trap is not a call and a switch is.** The interrupted program of [ch16](#traps-and-system-calls) agreed to
nothing, so everything it might have been using has to be preserved. `swtch` is reached by an
ordinary `jal` from `sched`, which means [ch14](#machine-level-code-on-riscv)'s calling convention has already been
obeyed on the way in: anything the caller cared about and the convention does not protect is
already spilled to the caller's stack. What is left for the switch to keep is exactly the
callee-saved set, plus the return address and the stack pointer — fourteen registers, and the
structure that holds them has fourteen fields.

So the cost of a switch is low for the same reason the cost of a trap is high, and neither number
is a property of how well the code was written. They are properties of who agreed to what.

### Where the thread goes

`swtch` takes two pointers, saves into the first and restores from the second, and returns — but
it returns somewhere else. The `ret` at the end reads the `ra` that was just loaded from the
*other* context, so control arrives in whichever function last called `swtch` on that side. A
thread's identity, at the instruction level, is a saved stack pointer and a saved return address.
Everything else about it is in memory that neither of those moves.

This is also the answer to [ch20](#locks-and-memory-ordering)'s impossibility. The lock is held by a *process*, and the
process's state lives in memory that both harts can reach. `swtch` does not release anything and
does not need to: the acquire and the release are operations on a shared word, and which core
performs them is not part of the agreement. What would break is holding a lock across a switch
*and* expecting interrupts to stay disabled on the hart you came from — which is why `push_off`
and `pop_off` count nesting per CPU rather than per process, and why [ch20](#locks-and-memory-ordering) found them
costing more instructions than the lock.

### Why did it switch?

Every switch out of a process goes through one function, so counting them is easy. Attributing
them is the interesting part, and the patch records which of three reasons applied: the timer took
the CPU away, the process is waiting for something, or the process is not coming back.

```{include} _generated/scheduling-and-context-switches-census.md
```

Only the last is a number the workload decides. A process that exits switches away exactly once,
and the count is the children the workload created plus the workload itself.

The other two are declined, and by now the reason should be familiar: a count of how often the
timer intervened is a statement about elapsed time, and a count of how often something waited
depends on whether the thing it waited for had already happened. [ch19](#interrupts-and-drivers) established this
for devices and it is the same argument.

One observation is worth having even though it is not in the table. In this workload the timer
**never** took the CPU away from anything: every switch was voluntary, because every process
blocked or exited before its slice ran out. Preemption is what a scheduler is for, and a
short-lived workload of blocking processes never needs it. Problem 21.3 is about what a policy
decides when preemption does happen; running the census yourself and trying to make the timer
intervene is a more instructive ten minutes than reading about it.

### Sleeping is not a state of the CPU

[ch19](#interrupts-and-drivers)'s console driver slept, and this is where that gets settled.

Sleeping is not the hardware doing anything. It is a process marking itself not-runnable, noting
what it is waiting for, and calling `sched` — after which some other thread's registers are in the
CPU and the sleeper exists only as a `struct context` in memory. Waking is the reverse: somebody
marks it runnable again, and eventually the scheduler picks it up and `swtch`es back into it, and
it returns from a function call it made an arbitrary time ago.

The dangerous part is the gap. If the sleeper checks a condition, finds it false, and then sleeps,
a wakeup arriving in between hits a process that is not yet asleep, hits nothing, and is not
repeated. That is a lost wakeup, it is the reason sleep is handed the lock that guards the
condition rather than being called after releasing it, and problem 21.2 is about being able to
spot it in an ordering rather than recognising it in a diagram.

## What we measured

What `swtch` moves, read out of the kernel as built, and the one switch count this workload fixes.
Nothing was timed: what a switch *costs* is the registers, the cache lines they touch, and what
the new thread finds missing when it starts running — and only the first of those is visible here.
[ch29](#the-os-layers-cost) measures the rest.

## What this cannot tell you

**What a switch costs.** Two hundred and twenty-four bytes move; whether that is expensive depends
entirely on whether they are in cache, and this target has no cache. The expensive part of a real
context switch is usually not the registers at all — it is that the new thread arrives to find the
caches and the TLB full of somebody else's data. [ch29](#the-os-layers-cost) is where that gets a number, and
the number is not small.

**Whether xv6's scheduler is any good.** It is a round-robin over a fixed array, chosen to be
readable, and it is not trying to be anything else. Real schedulers care about fairness over time,
about which core a thread last ran on, and about latency for threads that have just been woken;
none of that is in forty lines and none of it is visible in a switch count.

**Anything about more threads than cores.** This workload never had enough runnable processes to
make the scheduler choose, which is why the timer never intervened. A measurement of scheduling
needs contention for the CPU, contention is a question about time, and this chapter has spent its
whole length explaining why that question goes to [Part V](#part5).

**What `sched` does about the lock, exactly.** The dance between `sched`, `scheduler` and
`p->lock` is the subtlest twenty lines in xv6 and is worth reading with the invariants in front of
you — they are written in the comments. This chapter has said what the switch moves; it has not
tried to prove the locking correct.

## Problems

Three, in `tests/scheduling_and_context_switches/scheduling.c`.

**21.1 — Must the switch save this register?**
Given the register's role under [ch14](#machine-level-code-on-riscv)'s convention and whether the value is still needed,
say whether `swtch` itself has to preserve it.

The whole question is that a context switch is an ordinary call, so most of the answer was settled
seven chapters ago. Getting it right is what makes the fourteen against thirty-one above obvious
rather than surprising.

```bash
python3 -m pytest tests/scheduling_and_context_switches/test_problem_1_save.py
```

**21.2 — Does the sleeper wake?**
Six event sequences; say which loses a wakeup. Two of them use exactly the same six events in
different orders and have different answers, which is the entire lesson.

```bash
python3 -m pytest tests/scheduling_and_context_switches/test_problem_2_wakeup.py
```

**21.3 — What order does each policy run them in?**
Three jobs, three policies, three different answers. First-come-first-served, shortest-job-first
and round-robin with a quantum of one, on burst lengths chosen so that no two policies agree.

Producing the orders is mechanical; the value is in noticing what each one optimises and what it
gives up, and that shortest-job-first needs to know something the kernel cannot generally find out.

```bash
python3 -m pytest tests/scheduling_and_context_switches/test_problem_3_policy.py
```

## Where to go next

xv6's `kernel/proc.c` @xv6-riscv-source — `scheduler`, `sched`, `yield`, `sleep` and `wakeup` are
about a hundred lines between them and are now readable in full. The comment above `sched` stating
the invariants it requires is the densest paragraph in the kernel; read it after problem 21.2 and
it will say something it would not have said before.

`kernel/swtch.S` is the fourteen stores and fourteen loads this chapter counted, and was the
fourteen lines [ch14](#machine-level-code-on-riscv) sent you to look at without explaining. It has not changed; you have.

[ch22](#the-file-system) is the last of [Part IV](#part4) and the one with a disk in it. A file system has to survive
being interrupted at any instruction by a power cut, which is a stronger requirement than anything
a lock provides, and it is met by writing things down in an order chosen so that every prefix of
the sequence is survivable.
