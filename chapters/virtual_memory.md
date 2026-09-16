---
title: "Virtual Memory"
short_title: "17 · Virtual Memory"
---

(virtual-memory)=
# 17 · Virtual Memory

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch16](#traps-and-system-calls) |
| **What it measures** | The page-table shape of a running process: levels, entries, and physical pages consumed per mapping: `bench/results/pagetable-xv6.json` |
:::

## The question

What is an address, and who decides what it means?

Every chapter so far has treated an address as a number that names a place. [ch15](#linking-and-loading) watched
a loader put a program at the address its linker chose, and [ch16](#traps-and-system-calls) left a promise: the
trampoline page is mapped into two address spaces at once, which is only a sentence anybody can
say if an address means different things to different programs. It does. This chapter is about the
machinery that arranges it, and about what that machinery costs — not in time, which this target
cannot tell you, but in the memory it takes to say where memory is.

## The material

### An address is a question

The instruction `ld a0, 0(a1)` does not name a location. It names a number, and something between
the core and the memory has to decide what that number refers to. On this machine the decision is
made by a data structure in memory, and one register says where that structure begins.

That register is `satp`. Writing to it replaces every address in the running program's world at a
stroke, which is why [ch16](#traps-and-system-calls)'s trap path switches it and why the trampoline has to be mapped
at the same address in both maps — the instruction after the switch has to still exist.

So "what is an address" has a precise answer. **An address is a question, `satp` names who
answers, and the answer is looked up rather than computed.**

### Nine, nine, nine, twelve

The scheme is called Sv39, and the temptation is to learn its layout as a fact. It is not a fact;
it is forced, and two decisions force it.

Choose a page size, and choose how big an entry describing a page must be. Everything else
follows: a table is one page of entries, so the number of entries per table is one divided by the
other, and the number of bits needed to index a table is the logarithm of that. Stack enough
levels to reach a useful address width and you have the whole design.

```{include} _generated/virtual-memory-sv39.md
```

Read the right-hand column. Only the first two rows were chosen. Nine bits per level is not a
tuning parameter — it is what a 4096-byte page holding 8-byte entries makes you use, and a
designer who picked a different page size would get a different number of levels rather than a
different number of bits.

```{figure} _figures/virtual-memory-walk.svg
:alt: A 64-bit virtual address split into three nine-bit indices and a twelve-bit offset.
:width: 100%

One virtual address, and the four things translation does with it.
```

Two details in that figure repay attention.

**The offset is not translated.** The bottom twelve bits are copied from the virtual address to
the physical one, untouched. Translation moves pages about; it has no opinion about where in a
page a byte is. That is why a page is the unit of everything in this chapter: it is the smallest
thing the mechanism can say anything about.

**The top twenty-five bits are not spare.** Sv39 translates thirty-nine bits, and the rest of the
word must all copy bit 38 — a sign extension, exactly as in [ch13](#representing-information). An address that fails
that rule is not an address that is out of range; it is not an address, and the hardware refuses
it. xv6 declines to use the top half at all, capping its address space one bit below the maximum
so that every address it ever forms has bit 38 clear and the question never arises.

### A fault is a walk that stopped

Follow the indices down and one of three things happens. An entry with its valid bit clear ends
the walk. An entry with valid set and none of read, write or execute points at the next table
down. An entry with valid set and any of them is a leaf, and the walk is over.

The useful consequence is that **a failed translation has a location**. It is not "this address is
wrong" but "the walk got this far and stopped", and which level it stopped at says something
different each time. Stopping at the top level means nothing in that gigabyte of the address space
exists. Stopping at the bottom means the neighbourhood is mapped and this particular page is not —
a stack that has grown one page too far, say, rather than a wild pointer. [ch18](#page-faults-as-a-feature) is about
what a kernel can do with that distinction; problem 17.3 is about extracting it.

### Two clusters and five tables

Here is where the chapter stops describing and starts counting.

`init` is the first program xv6 runs, and the smallest interesting address space in the system. It
maps six pages. Describing those six pages takes five more.

```{figure} _figures/virtual-memory-address-spaces.svg
:alt: init's two clusters of mapped pages, and the chain of tables each one forces.
:width: 100%

Why six mapped pages need five pages of table.
```

The six are not in one place. Four are at the bottom of the address space, where the linker put
the program. Two are at the very top: the trapframe and the trampoline, which [ch16](#traps-and-system-calls) put
there. Those two clusters are separated by almost the whole of a 512-gigabyte address space, so
neither can reuse any of the other's tables — each forces its own chain down from the shared root.

A chain is two pages whether it ends in one mapping or five hundred.

### The map costs memory

Which makes the totals worth putting side by side.

```{include} _generated/virtual-memory-shape.md
```

The kernel maps an enormous amount of memory and spends almost nothing per page describing it.
init maps almost nothing and spends nearly as much on the description as on the thing described.
That inversion is not a paradox once the last column is read as the explanation for the other two:
the kernel's memory arrives in a handful of vast runs, and init's in two tiny ones.

Two of the kernel's regions account for nearly everything it maps. One is the whole of the RAM it
manages, direct-mapped so that a physical address and a kernel virtual address are the same
number — which is not a cheat but a decision, and one that makes the kernel's own pointers
translatable without any bookkeeping at all. The other is a run of device registers so long that
three separate devices, laid out end to end by the machine's designers, come out as a single
region: the census cannot tell them apart, because as far as the page table is concerned they are
not different things.

Almost every remaining region is a single page, and they are kernel stacks. xv6
leaves an unmapped page between every pair of them, so that a kernel stack which overflows hits
nothing rather than quietly writing into its neighbour. Each of those guard pages costs nothing —
an absent mapping is an entry that is not there — and the arrangement costs one shared table for
the lot, because they are all in the same two megabytes.

### The most expensive two pages in the system

Go back to init's five tables and ask which mapping is responsible for which.

The four pages at the bottom need a chain: root, one middle table, one last table. Three pages of
table for four pages of program, and every further page the program allocates is free until it
crosses two megabytes.

The two pages at the top need another middle table and another last table, because nothing else is
within a gigabyte of them. Two pages of table for two pages of mapping, and every process in the
system pays it.

**Those two pages are the trapframe and the trampoline.** The mechanism [ch16](#traps-and-system-calls) measured in
instructions has a second price, in a currency that chapter had no way to express: per process, two pages
of table, for as long as the process exists. Neither number is a cost in the sense this book
usually means — [ch29](#the-os-layers-cost) is where traps get priced in time — but both are real, and the
second one is invisible unless somebody counts it.

### The model and the kernel

One more thing is worth saying about how the numbers above were obtained, because it is not the
usual thing.

The kernel counts its own tables by walking them. Separately, `sysfs/tools/sv39.c` computes how
many tables a set of mappings *requires*, from the addresses alone, with no machine involved:

```{literalinclude} ../sysfs/lib/sv39.c
:language: c
:start-at: uint64_t sysfs_sv39_tables
:end-before: out[2] = 1;
```

The two are arrived at from opposite ends — one by inspecting a running system, the other from a
specification — and the runner refuses to record a result in which they disagree. So the figures
above are not a measurement that happens to be reproducible. They are an agreement, and if a
future xv6 changes its layout the disagreement is what CI will report.

## What we measured

The shape of two address spaces: how many pages of table each spends, how many pages each maps,
and how many separate regions those pages fall into. Both are structural constants rather than
anything a particular run produced — the kernel's map is built once from a layout fixed at compile
time, and init's is built by `exec` from a binary whose size the linker decided.

The shell's address space is deliberately not recorded. xv6's shell calls `malloc` while it parses
a command, so its size is a fact about what it has been asked to do rather than about address
spaces, and [ch16](#traps-and-system-calls) already spent a commit learning what happens when those two get
confused.

## What this cannot tell you

**What a translation costs.** Nothing here is a duration, and the omission is not a limitation of
effort. Translation is done by hardware that caches its results in a TLB, and QEMU models neither
the cache nor the miss — so a walk measured here would take exactly as long as the emulator's
bookkeeping and tell you about the laptop. [ch25](#the-memory-hierarchy) measures what a miss costs on a machine
that can charge for one, which is also where the three levels stop being free: a miss is not one
memory access, it is up to three, before the access you asked for.

**Whether a bigger page would help.** Sv39 allows a leaf at the middle or top level — a two-
megabyte or one-gigabyte mapping — and the census counts leaves by level precisely so that this
would be visible. It counted none: xv6 never makes one. Whether that costs anything is a question
about TLB reach, and this target has no TLB. The measurement above is honest about the format
supporting superpages and says nothing about whether using them is a good idea.

**Anything about permissions.** Every entry carries read, write, execute and user bits, and this
chapter counted entries without looking at them. What those bits prevent, and what a kernel does
when one of them is violated, is [ch18](#page-faults-as-a-feature).

**What a real system's address space looks like.** init maps six pages; a browser tab maps
hundreds of thousands, in hundreds of regions, most of them nowhere near each other. The overhead
column would look quite different, and the mechanism producing it is identical — which is the
reason this chapter measured the small case, where every page of table can be accounted for by
hand.

## Problems

Three, and they are one program: `tests/virtual_memory/walk.c` builds a page table, follows it, and reports
where following it stops. Nothing in `sysfs/` does any of those, so the repository contains no
answer to any of them.

**17.1 — Build a page table, and no more of one than the addresses require.**
Write `walk_map`, allocating interior tables as you need them.

The grading is the interesting part. The test does not compare your table with a stored one; it
counts how many pages you took from the allocator and compares that with what this chapter's own
model derives from the addresses. Three address spaces are used, each with the same number of
pages arranged differently, and they cost three different amounts. An implementation that
allocates eagerly maps everything correctly and still fails — which is this chapter's claim,
turned into a check.

```bash
python3 -m pytest tests/virtual_memory/test_problem_1_map.py
```

**17.2 — Follow it.**
Write `walk_translate`. The expected answers are the mappings the test asked your own 7.1 to make,
so the target moves with your implementation rather than being a constant. Two things are easy to
get wrong and are checked: the offset must survive, and an address that was never mapped must
fault rather than returning something plausible.

Handle a leaf found above the bottom level even though 7.1 never creates one. The format allows
it, and code that assumes otherwise is wrong in a way that will not show up until it meets a
kernel that uses superpages.

```bash
python3 -m pytest tests/virtual_memory/test_problem_2_translate.py
```

**17.3 — Say where it stopped.**
Write `walk_first_missing_level`. Four probes: one mapped, and one each for a walk that fails at
the top, the middle and the bottom. Each answer follows from where the test put the mappings, so
there is nothing to look up.

This is the function a page-fault handler needs before it can decide anything, and [ch18](#page-faults-as-a-feature)
is about the decisions.

```bash
python3 -m pytest tests/virtual_memory/test_problem_3_fault.py
```

## Where to go next

The RISC-V privileged specification @riscv-isa-privileged defines Sv39 in about four pages:
the entry format, the walk, and the rules about which reserved encodings fault. Read it after
problem 17.2 rather than before — the specification is describing something you will by then have
built, and it is much shorter than it looks.

xv6's `kernel/vm.c` @xv6-riscv-source is now readable in full. `walk` is the function you wrote
twice, with one extra argument that makes it do both jobs; `mappages` is a loop around it;
`freewalk` is the same traversal a third time, and the census this chapter added is a fourth.
Four uses of one traversal is a good thing to notice about a kernel.

[ch18](#page-faults-as-a-feature) takes the failure case seriously. A walk that stops is an opportunity, not an
error — and a kernel that treats it that way can hand out memory it has not allocated, share pages
until somebody writes to one, and keep a program's whole address space on disk.
