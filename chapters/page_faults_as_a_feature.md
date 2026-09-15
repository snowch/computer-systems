---
title: "Page Faults as a Feature"
short_title: "16 · Page Faults as a Feature"
---

(page-faults-as-a-feature)=
# 16 · Page Faults as a Feature

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch15](#virtual-memory) |
| **What it measures** | Pages allocated and faults taken for one workload, under each of the kernel's two allocation policies: `bench/results/faults-xv6.json` |
:::

## The question

What can a kernel do with a fault it expected?

[ch15](#virtual-memory) ended with a walk that stopped and a level to report it at. That was presented as a
diagnosis, which is how a fault is usually introduced: something went wrong, and here is where.
But a walk stops whenever an entry is absent, and **the kernel decides which entries are absent**.
So a kernel can arrange to be told, by hardware, at the exact moment a particular address is
touched — and the question stops being what went wrong and becomes what to do about it.

## The material

### The hardware will call you

Strip away the vocabulary and a page fault is a callback with three unusual properties.

It is **precise**: the kernel is given the address, in `stval`, not merely told that something
happened. It is **synchronous**: it happens at the instruction that touched the address and not
at some convenient later point. And it is **unavoidable**: the program cannot opt out, because it
does not know it is happening.

No other mechanism in the machine has all three. A timer interrupt is not precise. A system call
is not unavoidable — the program has to make it. This is the only way to have code run exactly
when a particular byte is used, and everything in this chapter is built on that one property.

### The instruction runs again

Here is the difference from [ch14](#traps-and-system-calls) that makes it work, and it is one line of the kernel.

After a system call, `usertrap` advances the saved program counter past the `ecall` before
returning, because the call has been made and the program should carry on with the next
instruction. After a page fault it does not. The saved program counter still points at the load or
store that faulted, so returning from the handler **runs that instruction again**.

Which is exactly what you want and is easy to miss the significance of. The handler does not
emulate the access, does not need to know what the instruction was, and does not have to put a
value anywhere. It makes the address work and returns, and the hardware does the rest. A fault
handler is therefore allowed to be ignorant of almost everything about the program it is rescuing.

```{figure} _figures/page-faults-as-a-feature-decision.svg
:alt: A page fault, the one test that decides what happens, and the two outcomes.
:width: 100%

What the kernel does with a fault, and the single question that decides it.
```

### One test, and the one next to it

xv6's handler asks whether the faulting address is below the process's size. Below it, the process
asked for this memory and has not touched it yet, so the right answer is to allocate a page, map
it, and return. At or above it, the process is using an address it never requested, and the right
answer is to kill it.

There is a second test beside it that is easier to leave out. If the page is *already* mapped, the
fault cannot be a first touch — the entry is there and valid, so the walk did not stop for lack of
one. It stopped because a permission was refused. Allocating a fresh page for that case would map
a blank page over one the program was in the middle of using, and the program would not crash; it
would get the wrong answer. Problem 8.2 is about exactly these edges.

### Both policies are already here

This is unusual enough to be worth stating plainly: **this kernel already implements both
allocation policies**, and lets a program pick one per call. `sbrk` allocates the pages when you
ask. `sbrklazy` increases the process's size and allocates nothing, leaving the faults to do it.

So this chapter adds no policy and changes no decision. The patch counts:

```{literalinclude} ../xv6/patches/15-fault-census.patch
:language: diff
:start-at: +census_page(int lazy)
:end-before: +void
```

Per process, because the shell is allocating too and a global total would mostly be a fact about
the shell. Latched on the way out, because by the time anybody can press a key the interesting
process has exited.

### The trade, counted

The workload asks for memory both ways and touches a known amount of it:

```{literalinclude} ../xv6/apps/faultload.c
:language: c
:start-at: int main(void)
:end-before: printf("faultload
```

Build it into the kernel, boot, and run it:

```bash
./run faultload
```

Three phases, chosen to bracket the trade rather than to demonstrate a win. A large lazy request
barely touched; a lazy request touched in full; an eager request of the same size as the first.

```{include} _generated/page-faults-as-a-feature-exchange.md
```

Read the first four rows as one sentence. Most of what was asked for lazily was never allocated,
and the pages that were allocated each cost one entry into the kernel — the whole of [ch14](#traps-and-system-calls)'s
trap path, plus a walk, plus an allocation, for every one of them.

That is the exchange rate, and it is the thing usually left out. Laziness is nearly always
described by its saving, and the saving here is real and large. The price is real too: a number of
kernel entries equal to the number of pages the program actually uses. Which of those matters
depends entirely on the ratio between them, and that ratio is a property of the program rather
than of the policy.

The last row is a different kind of fact and worth a moment. Before `main` ran at all, `exec` had
already allocated pages for the program's text, its data and its stack. Every process pays that,
and it is the baseline everything else in the table sits on top of.

### Which fault, and what this kernel does about it

The hardware does not report "a page fault". It reports a load fault, a store fault or an
instruction-fetch fault, as three different causes.

```{include} _generated/page-faults-as-a-feature-causes.md
```

Every page in this run arrived on a store, because the workload writes to each page it touches. A
program that read a lazily-allocated page before writing it would produce load faults instead, for
the same pages.

And this kernel does nothing with the difference: both causes are handled identically and get a
readable, writable page. That is a real observation about xv6 rather than a gap in the
measurement — the distinction exists in the hardware, and using it is what copy-on-write is. A
kernel that shares a page between two processes marks it read-only in both, at which point a load
fault cannot happen and a store fault means *somebody is about to modify a page they are
sharing*. Same hook, same handler, one more test.

### What laziness costs that is not faults

There is a second price, it is not measured in pages or in faults, and it is the one that has
consequences outside this chapter.

An eager request that cannot be satisfied fails at the call. The program gets a return value it
can test, and can do something sensible — free a cache, use a smaller buffer, report a clear
error. A lazy request always succeeds, because nothing has been allocated and there is nothing to
fail. The shortage is discovered later, by a store instruction, in the middle of code that has no
idea it is allocating anything. There is no return value to check at that point, and nothing the
kernel can do but kill the process.

So laziness moves a failure from a place where the program can handle it to a place where it
cannot. That is the whole reason an operating system which overcommits memory needs a policy for
choosing something to kill, and problem 16.3 is about being able to say precisely when each
version finds out.

## What we measured

Pages allocated and faults taken for one workload, under each of the kernel's two policies, with
every quantity fixed by the program rather than observed to be steady. `faultload` prints what it
asked for and what it touched; the kernel counts independently; the runner refuses to stamp a
result in which the two disagree, refuses one latched from a different process, and refuses one in
which the handler declined a fault — which would mean the workload went somewhere it never asked
for, and that the numbers describe a bug rather than a policy.

## What this cannot tell you

**What a fault costs.** Not a single duration appears above, and it could not honestly. A fault's
cost is the trap path, the walk, the allocation and whatever the TLB and the caches make of the
interruption — and this target models none of the last part. [ch27](#the-os-layers-cost) prices the whole shape
on hardware. Until then, "seventeen faults" is a count of kernel entries and not a claim about
time.

**Whether laziness is worth it.** The table gives the exchange rate for one workload, chosen to
show both ends. Whether trading those pages for those faults is a good deal depends on how much
memory costs relative to kernel entries on the machine in question, which is a question about
hardware and not about kernels.

**Copy-on-write, demand paging, and the rest.** The chapter names them and measures none of them,
which is deliberate and is not the same as their being free. Each is this hook with a different
test, and each has its own exchange rate that this chapter has not measured. Naming a mechanism
and pricing it are different things, and the book tries hard not to let the first pass for the
second.

**Anything about fragmentation.** Every page here is the same size and comes from a free list that
does not care which one it hands out. A system where physical contiguity matters — for large
pages, or for a device doing its own addressing — has an allocation problem this one does not,
and no measurement here would notice.

## Problems

Three, in `tests/page_faults_as_a_feature/policy.c`. They are the three decisions the handler is really making, taken
out of the kernel so that being right about them is separable from getting a kernel to boot.
Neither this chapter's patch nor anything in `sysfs/` answers any of them: the patch counts and
decides nothing.

**16.1 — How many faults will these accesses cause?**
You are given runs of bytes a program touches and asked for the number of first-touch faults.

The trap is the one the whole chapter rests on: a program thinks in bytes and the machine charges
pages. Two accesses in one page cost one fault; an access of two bytes can cost two. The runs
overlap, repeat and arrive in no order.

```bash
python3 -m pytest tests/page_faults_as_a_feature/test_problem_1_faults.py
```

**16.2 — What should the handler do about this fault?**
Allocate, kill, or refuse to have an opinion. Nine cases, and three of them are the ones a handler
written from the happy path gets wrong: the exact boundary, a page that is already mapped, and a
cause that is not a page fault at all.

```bash
python3 -m pytest tests/page_faults_as_a_feature/test_problem_2_action.py
```

**16.3 — When does a program that asks for too much find out?**
For each policy, say where the shortage becomes visible: at the request, at the touch, or never.

This is the section above, turned into a function. Getting it right means you can predict which
of two programs — identical apart from one argument — dies in a way its author can do something
about.

```bash
python3 -m pytest tests/page_faults_as_a_feature/test_problem_3_observed.py
```

## Where to go next

The RISC-V privileged specification @riscv-isa-privileged lists the fault causes and says exactly
what the hardware guarantees about `stval` and about the state at the point of a fault. The
guarantee that the faulting instruction has had no effect is the one worth reading carefully; it is
what makes re-running it safe, and it is not free for the hardware to provide.

xv6's `vmfault` in `kernel/vm.c` @xv6-riscv-source is the handler this chapter measured, and it is
shorter than this section. Read it beside `sys_sbrk` in `kernel/sysproc.c`, which is where the two
policies are chosen between — the whole difference is one branch.

[ch17](#interrupts-and-drivers) stays with the same mechanism and changes what raises it. A page fault is the CPU
interrupting itself about something it was doing; a device interrupt is somebody else entirely,
with no relationship to the instruction that happens to be running, and that difference turns out
to matter more than it sounds.
