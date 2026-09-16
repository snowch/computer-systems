---
title: "Appendix H — Choosing the Machine"
short_title: "Appendix H"
---

(appendix-h)=
# Appendix H · Choosing the Machine

An appendix in this book is a reference, not a chapter. This one is read once, before you spend
any money, and then only to settle an argument with a spec sheet.

[Part V](#part5) is the only part that needs hardware of its own: it is where every number in the
book is measured, and [ch01](#setting-up-the-board) is where you make it work. What follows is
the decision before that — what the `host` target has to be able to do, how to check a machine you
already own, and what changes if yours differs from the reference. The *argument* for a second
machine at all is in the preface; this is the shopping and the checking.

A **Raspberry Pi 5 with 4 GB or more**, and an active cooler. That is the whole decision. Every Pi
5 has the counters this book needs — same SoC, same four cores, no variant where they are missing
— so there is no specification to compare and nothing to get wrong except the RAM, and only
because [ch28](#memory-ordering-on-real-hardware) wants four cores with room to work.

| | What | Why this one |
|---|---|---|
| **Board** | Raspberry Pi 5, 4 GB or 8 GB | Four identical Cortex-A76 cores whose performance counters work. See below |
| **Cooling** | The official active cooler, or a case with a fan | **Not optional here.** A Pi 5 under sustained load throttles |
| **Power** | The official 27 W USB-C supply, or one rated for the board | Underpowering a Pi produces instability that reads exactly like a kernel bug |
| **Storage** | A microSD card that is not the cheapest on the shelf | An NVMe drive on a PCIe HAT is nicer and not required |
| **Network** | An Ethernet cable — any working one | WiFi works. Wired keeps the radio's driver from doing interrupt work on the cores you are measuring |

You also need a development machine for Parts I to IV — anything that runs Homebrew or apt and
holds an SSH key. It never measures anything.

**The cooler earns its line in the table.** A Pi 5 that throttles is running a benchmark at one
clock speed and finishing it at another, which is not a slow measurement but a wrong one, and one
of the more instructive ways to be wrong. [ch24](#measuring) treats throttling as a measurement hazard
and shows how to catch it happening; a cooler means you meet it deliberately rather than in every
run you ever take.

## Why a separate board, and not the laptop you are reading this on

A laptop can almost certainly count and sample — `perf` on x86-64 is mature, and on Linux you
could start [Part V](#part5) this afternoon. The reason not to is that the machine is too complicated to
learn on. A current laptop has cores of two different kinds, a clock that moves constantly, two
threads sharing one core's execution units, and a scheduler migrating your benchmark across all of
it. Each of those makes a measurement harder to attribute. The Pi 5 is four identical cores with
one cache hierarchy and no hyper-threading: when a number moves, something you did moved it.

That is the book's own argument applied to its own tooling — use the instrument that can answer
the question. A laptop is a *faster* machine and a *worse* instrument. If a Pi is genuinely not
possible, [Part V](#part5) still runs on a Linux laptop, and every chapter whose reading depends on the
core's shape says so in its own header.

The Pi is not the *most* legible instrument, and it is worth knowing what it is not. An **in-order**
core — short pipeline, no out-of-order execution, no register renaming — makes microarchitecture
plainer still: a dependent load that misses in cache stalls, visibly, for as long as the miss
takes. The A76 reorders, so the connection between an instruction you wrote and a cycle that got
spent runs through enough machinery that a small experiment occasionally comes out backwards.

Two reasons that is the right trade anyway. The in-order RISC-V option could not sample, which
cost more than legibility bought. And **every machine you are likely to care about optimising
reorders**, so learning to attribute cycles on one is the skill that transfers.
[ch27](#the-cpu) is harder for it, says so in its own header, and is more useful as a result. If you
want the clean version too, an in-order Cortex-A53 — a Pi 3 or Pi Zero 2 W — costs very little,
and running [ch24](#measuring)'s experiments on both is an instructive afternoon.

## It is an ARM machine, and everything before Part V is RISC-V

That is deliberate: `perf` has to both count *and* sample, no affordable RISC-V core does both,
and choosing one would have cost two chapters of [Part V](#part5). The [preface](#preface) has the evidence; this
chapter is about getting the machine working.

% number-ok: SoC specification from @rpi-bcm2712; every figure in this book comes from the machine itself
Its SoC is a BCM2712: four Arm Cortex-A76 cores at 2.4 GHz, 64 kB of L1 instruction and data
cache each, 512 kB of L2 per core, and 2 MB of L3 shared between them @rpi-bcm2712. Those are the
vendor's numbers, and the book does not repeat them anywhere else — [ch25](#the-memory-hierarchy) measures that
hierarchy rather than quoting it, and comparing what it finds against this paragraph is one of the
more satisfying results in [Part V](#part5).

Three levels with a private L2 and a shared L3 is a genuinely good shape to learn on. The private
level shows you locality; the shared one is where [ch28](#memory-ordering-on-real-hardware)'s cores collide.

## If you already own something else

The book recommends one machine because one machine is enough, not because the rest of [Part V](#part5)
is about Raspberry Pis. What a machine actually has to do is short:

| | Requirement | Why |
|---|---|---|
| **Must** | 64-bit Linux, reachable over SSH | |
| **Must** | `perf stat -e cycles,instructions -- true` returns real counts | **The one requirement with no workaround.** [Part V](#part5) does not exist without it |
| **Must** | `perf record` can sample | [ch30](#whole-machine-profiling) is entirely sampling. A different capability from counting |
| **Must** | 4 GB RAM, 4 cores | [ch28](#memory-ordering-on-real-hardware) measures what cores cost each other |
| **Nice** | NVMe or a fast SSD | Builds and [ch22](#the-file-system) are far less tedious |
| **Nice** | A SIMD unit the compiler targets — NEON, or RVV 1.0 | [ch31](#vectors) measures vectorisation |
| **Nice** | Few kinds of core, and a clock that holds still | Not required. It is why the reference is a Pi rather than a laptop |

An old laptop, a spare desktop, a Rock 5B, another single-board computer you have in a drawer: run
`scripts/verify-setup.py` on it and it will tell you. `hardware/README.md` has the same list in a
form you can hand to a search tool, for readers somewhere Raspberry Pis are hard to get.

:::{caution} The purchase is yours
This book does not sell hardware, has no relationship with any vendor, and has tested nothing but
its own reference machine. Prices, availability and listings change; nothing here is a warranty
that a given machine will work for you.

The practical version: **the requirement you cannot check before it arrives is the one that
matters most.** No product listing can honestly promise you working performance counters, because
they depend on the image as much as on the board. Buy somewhere with a return policy, and run
`scripts/verify-setup.py` on day one rather than the week you reach [Part V](#part5).
:::

## The requirement to be suspicious about

The counters. Everything else is printed on the box; whether `perf` can read the hardware is not,
and it is the one that stops the book dead.

On ARM the PMU is reached directly, but the kernel still has to be told it is there, and this is
not hypothetical: the Raspberry Pi kernel's own 6.12 branch shipped a device tree for the Pi 5
with the `arm-pmu` node missing @rpi-pmu-dt-6507. The 6.6 tree had it. On the affected images the
hardware was perfectly capable, the `armv8_cortex_a76` driver never registered, and `perf` saw no
hardware counters at all — quietly, because that is how this fails.

On RISC-V there is an extra layer: the counters are machine-mode CSRs, the kernel runs in
supervisor mode, and the firmware bridges them through the SBI PMU extension @riscv-sbi, so the
answer depends on the firmware as much as on the silicon.

Read that regression as the general case rather than a Raspberry Pi anecdote. **Whether your
counters work is a property of the configuration, not of the board** — silicon, device tree,
kernel, firmware and `perf` build all have to agree, and four of those five change under you
without the box changing at all.

:::{important} The book does not tell you which kernel to run
It would be easy to end this section with an image and a version number, and that would be worse
advice than it looks. A pinned version is wrong within a year, cannot be re-verified on every
release, and teaches you to check a string instead of a machine — while the failure it is meant
to prevent stays perfectly possible on the version that was correct when it was written.

A *minimum* version would be worse still, and the reason is specific rather than pedantic. What
went wrong on the Pi 5 was a **regression**, so the node was present in the older kernel and
absent in the newer one; a floor selects for the broken configurations rather than against them.
A range would work and would need maintaining forever — and it would still have to be written
once per kernel tree, because the Raspberry Pi kernel and mainline are different trees that
disagree about this today @rpi-dt-bcm2712. The version number is not the thing. The device tree
in `/boot/firmware/` is the thing, and your machine will read it out for you.

So the book does the other thing. Every `host` result stamps the board, the operating system, the
kernel and whether `perf` could count and sample, and the table at the end of this chapter is
that stamp. It tells you what produced the book's numbers; it is not a requirement for yours.
What is required is that `verify-setup.py` passes on the machine in front of you, which is a
question about that machine and not about a version string.
:::

## The reference machine, and why your numbers will differ

Every figure in [Part V](#part5) of this repository was measured on the machine that its result names —
each one stamps the model, the core and the kernel that produced it, so no figure is ambiguous
about where it came from.

So your numbers will not match, and that is expected rather than a problem. The book is about
ratios, mechanisms and method, and those transfer.

## Which chapters actually depend on the hardware

Most do not. Five chapters of [Part V](#part5) do, and rather than let you discover that two
hundred pages in, here they are up front. Each of these says the same thing in its own header, so you cannot open one without
being told.

| Chapter | What it assumes | What changes on a different machine |
|---|---|---|
| [ch25](#the-memory-hierarchy) | A particular cache hierarchy — levels, sizes, line size, TLB reach | The numbers, entirely. The method is the chapter, and measuring *your own* hierarchy is the exercise |
| [ch27](#the-cpu) | An out-of-order, 4-wide core, and the PMU events it exposes | Width, predictor and event names all differ. On an **in-order** core these experiments get easier to read, not harder |
| [ch28](#memory-ordering-on-real-hardware) | Four cores, and this interconnect's coherence behaviour | A different core count moves the scaling curve without changing the mechanism. Two cores make the chapter thin |
| [ch30](#whole-machine-profiling) | That `perf` can **sample**, not only count | Standard on a mainline ARM kernel. Most affordable RISC-V cores cannot, so this is the chapter a RISC-V reader will find they cannot run |
| [ch31](#vectors) | A vector unit — NEON here | On a RISC-V board without RVV 1.0 it reverts to reasoning about code the compiler emits but the hardware cannot run |

The pattern is worth noticing, because it is the same one the two targets follow. A chapter's
*mechanism* survives a change of hardware; its *numbers* do not. That is why the book insists on
stamping every figure with the machine that produced it, and why [ch25](#the-memory-hierarchy) is written as an
instruction rather than a table — a cache hierarchy you measured is worth more than one you read.

If none of your numbers resemble the committed ones and you want to know whether that is your
board or your method: it is almost always your board, and [ch24](#measuring) is where you learn to
tell the difference.

`hardware/README.md` has the requirements, the prompt and the verification step in one place, for
when you are standing in front of a shop rather than reading a chapter.

## The reference machine's own account of itself

Every figure in [Part V](#part5) was measured on one board, and what that board says about itself
is printed in [ch01](#setting-up-the-board) rather than here — it is the measurement that chapter
takes, and a statement about one piece of silicon rather than about a product line. Read it beside
the requirements above if you are comparing a machine you already own.

## Where to go next

`hardware/README.md` in the repository carries the same requirements as a checklist, plus the
evidence for choosing an ARM board over a RISC-V one: a 2025 study of the three RISC-V cores that
can actually be bought @riscv-pmu-profiling, and the counter-overflow extension a sampling
profiler needs @riscv-sscofpmf. [Appendix C](#appendix-c) is what this board turned out to
expose once it reported.
