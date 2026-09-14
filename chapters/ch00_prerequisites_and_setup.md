---
title: "Prerequisites and Setup"
short_title: "ch00 Prerequisites and Setup"
---

(ch00)=
# ch00 · Prerequisites and Setup

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` and `host` — every example says which |
| **Prerequisites** | none |
| **What it measures** | That both targets work, and exactly what they are: `bench/results/setup-xv6.json` and `bench/results/setup-host.json` |
:::

## The question

What do I need on my desk, and how do I know it works?

That second half is not a formality. Every later chapter rests on a claim about a machine — this
compiler, this kernel, these counters — and a setup that is *almost* right fails three chapters
later as something that looks like a bug in the material. So this chapter ends with a script that
interrogates the machine you are sitting at and tells you which of the book's two targets it can
currently run, and with two measurements that record what those targets actually are.

## Two targets, and what the repository does about it

The preface makes the case for the arrangement; this is the operational version of it.

**`xv6`** is the MIT teaching kernel under `qemu-system-riscv64`: a complete operating system in
about nine thousand lines, which you can stop mid-trap and inspect. Parts I and II live there, and
so does everything the book says about *what a program does*.

**`host`** is a small Linux machine on the desk, reached over SSH — a Raspberry Pi 5 in this book.
Everything about *what a program costs* is measured there, natively. Part III lives there.

The one thing worth repeating from the preface, because every later chapter depends on it: QEMU is
a functional emulator. It computes what the instructions compute and models nothing else — no
cache, no branch predictor, no store buffer, no pipeline, no memory latency. Ask it how long a loop
took and it will answer, and the answer describes the laptop QEMU was running on and the
translation strategy it happened to pick.

That generalises well beyond QEMU, which is why it is the first thing this book teaches: almost
every convenient way to observe a program changes what you are observing. A debugger stops it. A
profiler samples it. A print statement in a loop makes the loop something else. Knowing which of
your tools is lying to you about which question is the discipline underneath all of this.

So the repository enforces the split rather than trusting anyone to remember it. Every result
file records where it was measured, and `scripts/verify-numbers.py` rejects two things outright:
a `host` figure that was not produced natively on the hardware it claims, and an `xv6` result that
contains a duration at all.

```{literalinclude} ../bench/stamp.py
:language: python
:start-at: def provenance_problems
:end-before:     problems: list[str] = []
```

:::{note} You can start with one target
The xv6 target runs on any laptop and covers Parts I and II — fourteen chapters. If the Pi has
not arrived yet, set up the xv6 half now and come back to the rest before [ch13](#ch13). Nothing
in Parts I and II depends on hardware you do not have.
:::

## What to buy

A **Raspberry Pi 5**, 4 GB or more, **with the active cooler**. A Pi 4 you already own will do.

It is an ARM machine, and Parts I and II are RISC-V. That is deliberate: `perf` has to both count
and sample, no affordable RISC-V core does both, and choosing one would have cost two chapters of
Part III. The preface makes that argument with the evidence behind it; this chapter is about
getting the machine working.

% number-ok: SoC specification from @rpi-bcm2712; every figure in this book comes from the machine itself
Its SoC is a BCM2712: four Arm Cortex-A76 cores at 2.4 GHz, 64 kB of L1 instruction and data
cache each, 512 kB of L2 per core, and 2 MB of L3 shared between them @rpi-bcm2712. Those are the
vendor's numbers, and the book does not repeat them anywhere else — [ch15](#ch15) measures that
hierarchy rather than quoting it, and comparing what it finds against this paragraph is one of the
more satisfying results in Part III.

Three levels with a private L2 and a shared L3 is a genuinely good shape to learn on. The private
level shows you locality; the shared one is where [ch18](#ch18)'s cores collide.

**The active cooler is not optional for this book.** A Pi 5 under sustained load throttles, and a
benchmark that quietly changes clock speed half way through is not a slow measurement — it is a
wrong one, and one of the more instructive ways to be wrong about a benchmark. [ch14](#ch14)
treats thermal throttling as a measurement hazard and shows how to detect it; a cooler means you
meet it deliberately rather than by accident in every run.

### What the machine has to do

| | Requirement | Why |
|---|---|---|
| **Must** | 64-bit ARM or RISC-V running Linux, reachable over SSH | |
| **Must** | `perf stat -e cycles,instructions -- true` returns real counts | **The one requirement with no workaround.** Part III does not exist without it |
| **Must** | `perf record` can sample | [ch20](#ch20) is entirely sampling. A different capability from counting |
| **Must** | 4 GB RAM, 4 cores | [ch18](#ch18) measures what cores cost each other |
| **Nice** | NVMe or a fast SSD | Builds and [ch12](#ch12) are far less tedious |
| **Nice** | A SIMD unit the compiler targets — NEON, or RVV 1.0 | [ch21](#ch21) measures vectorisation |
| **Nice** | An in-order core | Not required, and the reference is out-of-order. See below |

Plus the unglamorous parts: a power supply **rated for the board** — underpowering one produces
instability that reads exactly like a kernel bug — a microSD card that is not the cheapest on the
shelf, and an Ethernet cable, because wired is one fewer variable when a measurement looks strange.

You also need a development machine for Parts I and II. Anything that runs Homebrew or apt and
holds an SSH key. It never measures anything.

### The requirement to be suspicious about

The counters. Everything else is printed on the box; whether `perf` can read the hardware is not,
and it is the one that stops the book dead.

On ARM the PMU is reached directly, but the kernel still has to be told it is there — some vendor
kernels have shipped without the PMU node in the device tree, and then `perf` silently sees no
hardware at all. On RISC-V there is an extra layer: the counters are machine-mode CSRs, the kernel
runs in supervisor mode, and the firmware bridges them through the SBI PMU extension @riscv-sbi,
so the answer depends on the firmware as much as on the silicon.

Either way the book's answer to "will this machine work?" is a script rather than a claim, and it
runs on the machine after it arrives rather than on a specification before it.

### Finding something else

If Raspberry Pis are hard to get where you are, the requirements above are stable but which
machines satisfy them today is not, and this book is the wrong place to answer it.

So `hardware/find-a-board.txt` states them in a form something else can shop against. Paste it
into an assistant that can search the web, with your country and budget filled in:

```{literalinclude} ../hardware/find-a-board.txt
:language: text
:start-at: HARD REQUIREMENTS
:end-before: NICE TO HAVE
```

That is an extract; the file also carries the RISC-V findings the preface sets out, so a
recommendation cannot walk you back into the problem those findings describe, and it asks for a
**source** for the `perf` claims specifically — the claim most likely to come back confidently
wrong.

:::{caution} The purchase is yours
This book does not sell hardware, has not tested most of what a search might surface, and has no
relationship with any vendor. Availability and prices change, listings go out of stock, and an
assistant will occasionally state a machine's `perf` support with more confidence than its
evidence supports. Verify the retailer, the price and the return policy yourself; nothing here is
a warranty that a given machine will work for you.

The practical version: the requirement you cannot check before it arrives is the one that matters
most. Buy somewhere that takes returns, and run `scripts/verify-setup.py` on day one rather than
the week you reach Part III.
:::

### On in-order cores, and why the reference is not one

An in-order core — short pipeline, no out-of-order execution, no register renaming — makes
microarchitecture *legible*. A dependent load that misses in cache stalls, visibly, for as long as
the miss takes. On an out-of-order core the connection between an instruction you wrote and a
cycle that got spent is mediated by enough machinery that small experiments sometimes come out
backwards.

The reference machine is out-of-order anyway, and there are two reasons that is acceptable.

The first is that the in-order RISC-V option could not sample, which cost more than legibility
bought. The second is more interesting: **every machine you are likely to care about optimising is
out-of-order.** Learning to attribute cycles on a core that reorders them is the skill that
transfers to the laptop and the server. [ch17](#ch17) is harder to read for it, says so in its own
header, and is more useful as a result.

If you want the clean version too, an in-order ARM core — a Cortex-A53, in a Pi 3 or Pi Zero 2 W —
costs very little, and running [ch17](#ch17)'s experiments on both is an instructive afternoon.

### The reference machine, and why your numbers will differ

Every figure in Part III of this repository was measured on the machine that its result names —
each one stamps the model, the core and the kernel that produced it, so no figure is ambiguous
about where it came from.

So your numbers will not match, and that is expected rather than a problem. The book is about
ratios, mechanisms and method, and those transfer.

### Which chapters actually depend on the hardware

Most do not. Five do, and rather than let you discover that two hundred pages in, here they are
up front. Each of these says the same thing in its own header, so you cannot open one without
being told.

| Chapter | What it assumes | What changes on a different machine |
|---|---|---|
| [ch15](#ch15) | A particular cache hierarchy — levels, sizes, line size, TLB reach | The numbers, entirely. The method is the chapter, and measuring *your own* hierarchy is the exercise |
| [ch17](#ch17) | An out-of-order, 4-wide core, and the PMU events it exposes | Width, predictor and event names all differ. On an **in-order** core these experiments get easier to read, not harder |
| [ch18](#ch18) | Four cores, and this interconnect's coherence behaviour | A different core count moves the scaling curve without changing the mechanism. Two cores make the chapter thin |
| [ch20](#ch20) | That `perf` can **sample**, not only count | Standard on a mainline ARM kernel. Most affordable RISC-V cores cannot, so this is the chapter a RISC-V reader will find they cannot run |
| [ch21](#ch21) | A vector unit — NEON here | On a RISC-V board without RVV 1.0 it reverts to reasoning about code the compiler emits but the hardware cannot run |

The pattern is worth noticing, because it is the same one the two targets follow. A chapter's
*mechanism* survives a change of hardware; its *numbers* do not. That is why the book insists on
stamping every figure with the machine that produced it, and why [ch15](#ch15) is written as an
instruction rather than a table — a cache hierarchy you measured is worth more than one you read.

If none of your numbers resemble the committed ones and you want to know whether that is your
board or your method: it is almost always your board, and [ch14](#ch14) is where you learn to
tell the difference.

`hardware/README.md` has the requirements, the prompt and the verification step in one place, for
when you are standing in front of a shop rather than reading a chapter.

## Setting up the machine

A Pi is a well-trodden path and the Raspberry Pi documentation is the authority on it. What
follows is the shape of the task and the parts this book depends on.

**1. Write a 64-bit image.** Raspberry Pi OS (64-bit) or Ubuntu Server for ARM, written with
Raspberry Pi Imager, which will also set the hostname, your SSH key and your WiFi while it
writes. Use its advanced options — it saves the whole "find it on the network and change the
default password" dance.

It has to be a **64-bit** image. A 32-bit userspace on ARMv7 does not get you the ARMv8 PMU, and
you would spend an afternoon finding that out.

**2. Boot it, wired if you can.** WiFi works; wired is one fewer variable when a measurement
looks strange.

**3. Give it a name.** In `~/.ssh/config` on your laptop:

```
Host bench
    HostName raspberrypi.local
    User pi
    ServerAliveInterval 30
```

Now `ssh bench` works, `make bench-board` over SSH works, and VS Code's Remote-SSH extension can
open it as a workspace — *Remote-SSH: Connect to Host…*, pick `bench`, and the editor runs its
file operations and its terminal there while the interface stays on your laptop. That is the
arrangement the rest of the book assumes: you edit on the laptop, and everything that touches a
counter happens on the machine being measured.

### The toolchain on the machine

```bash
sudo apt update
sudo apt install -y build-essential gdb git python3 python3-pip
```

`perf` is the awkward one. It ships as part of the kernel's own tooling, so the package that
provides it is tied to the running kernel. On Raspberry Pi OS:

```bash
sudo apt install -y linux-perf
perf --version
```

On Ubuntu, `linux-tools-$(uname -r)` or `linux-tools-raspi`. If the version `perf` reports does
not match `uname -r` it will still run, and will quietly fail to open some events — which is the
worst of the available outcomes, because it looks like the events do not exist rather than like a
broken tool. If nothing packaged matches, build it from the kernel source tree with
`make -C tools/perf` against the source for your running kernel.

### Proving the counters are real

This is the one capability Part III cannot work around, and it is worth being suspicious about,
because `perf` reports a failure to reach hardware in a way that is easy to skim past.

Ask:

```bash
perf stat -e cycles,instructions -- true
```

A working setup prints two counts. A broken one prints `<not supported>`, which means the event
never reached hardware — and if you are not reading carefully, a line saying `<not supported>` in
a column of numbers looks like a number. Worse, some configurations report a count of zero rather
than an error, and a zero is a number that will happily propagate into a table.

`bench/run_setup.py` therefore treats "counted" and "counted something greater than zero" as
different questions:

```{literalinclude} ../bench/run_setup.py
:language: python
:start-at: def perf_capability
:end-before:     if not shutil.which("perf")
```

If nothing is counted, the usual cause on ARM is that the kernel was never told the PMU exists —
the device tree needs a node for it, and some vendor kernels have shipped without one. Check
`dmesg | grep -i pmu` for a line claiming the driver bound, and
`ls /sys/bus/event_source/devices/` for a per-core PMU such as `armv8_cortex_a76`. On a RISC-V
machine the failure is usually further down: the counters are machine-mode CSRs reached through
the firmware's SBI PMU extension @riscv-sbi, so check for `CONFIG_RISCV_PMU_SBI` and a firmware
that provides it.

Until `perf stat` prints real counts, Part III cannot start, and no amount of care in the chapters
substitutes for it.

### Counting is not sampling

There is a second capability, and it is the reason this book's `host` target is an ARM machine.

`perf stat` **counts**: it totals events over a whole run. `perf record` **samples**: it
interrupts the program thousands of times a second to ask where it is, and builds a picture of
where the time went from those interruptions. Sampling needs the counters to raise an interrupt
when they overflow, and that is a separate hardware feature from counting.

```bash
perf record -o /dev/null -- true    # this must work too
```

On ARM, overflow interrupts are a standard PMU feature. On RISC-V they are the **Sscofpmf**
extension @riscv-sscofpmf, and a kernel on a core without it says so at boot and then declines:

```text
riscv-pmu-sbi: Perf sampling/filtering is not supported as sscof extension is not available
```

[ch20](#ch20) is entirely about sampling, so on a machine that cannot do it that chapter has
nothing to measure. `verify-setup.py` reports the two capabilities separately, precisely so you
find out now rather than three hundred pages in.

The distinction generalises well beyond RISC-V, which is why it is worth learning here: a
profiler that samples is answering a different question, with different failure modes, from a
counter that totals. [ch14](#ch14) takes that apart properly and [ch20](#ch20) depends on it.

## Setting up the xv6 target

On the Mac, via Homebrew:

```bash
brew tap riscv-software-src/riscv
brew install riscv-tools qemu
```

On a Debian or Ubuntu machine, including the board itself:

```bash
sudo apt install -y gcc-riscv64-linux-gnu qemu-system-misc qemu-user-static gdb-multiarch
```

`qemu-user-static` is worth installing even though no chapter requires it. It runs a cross-built
RV64 binary directly on an x86-64 or Apple-silicon machine, which means every `host`-target
example in Part III can be compiled and **checked for correctness** away from the board. It
cannot tell you anything about time, and the repository does not let it try — but it is the
difference between being able to work on Part III from a train and not.

### The repository

```bash
git clone --recursive https://github.com/snowch/computer-systems.git
cd computer-systems
python3 -m pip install -r requirements.txt -r requirements-dev.txt
```

`--recursive` matters: xv6 is a submodule, not a copy. If you have already cloned without it,
`make submodule` fixes it.

The submodule arrangement is deliberate. xv6 is MIT-licensed and copying it in would be perfectly
legal, but it would also hide what this book changes about the kernel. Instead the submodule stays
pristine — a test asserts that it is byte-identical to upstream — and the book's own material is
kept separately and combined into a staging tree at build time:

```
xv6/xv6-riscv/   upstream, never modified
xv6/apps/        the book's xv6 programs
xv6/patches/     the book's kernel instrumentation, as diffs
xv6/stage/       generated: all three, combined
```

So `ls xv6/patches/` is a complete answer to "what has this book done to the kernel?", and that
answer stays true. `xv6/README.md` has the mechanics.

### Booting it

```bash
make xv6-qemu
```

You should get a boot log, a shell prompt, and `ls` should list a couple of dozen programs.
`Ctrl-A X` quits QEMU; xv6 itself has no way to halt the machine, which is the first of many
small reminders that it is a teaching kernel and not a product.

The same thing non-interactively, which is how the tests do it:

```bash
python3 scripts/xv6-run.py -c ls -c sysprobe
```

## Checking the whole thing

```bash
python3 scripts/verify-setup.py
```

It reports each target separately, because most machines can run one of them. On a laptop it
confirms the cross compiler, QEMU, the submodule and a usable debugger, then explains that the
`host` target is read-only here and says whether an RV64 correctness path is available. On the
board it reads the device tree and `/proc/cpuinfo`, prints the ISA string and the core's vendor
and architecture IDs, and checks that `perf` reaches hardware.

Notice what it does *not* do: look anything up. Every fact it prints is read from the machine in
front of it. A specification describes a product line; `/proc/cpuinfo` describes the silicon that
is about to produce your numbers, and when the two disagree — which happens — the book cites the
one it measured.

### The same program in both worlds

The last check is the most interesting one, because it produces this chapter's first real result.

`sysfs/include/sysfs/probe.h` asks the machine a handful of questions it can answer without a
library: how big is each scalar type, where may it start, what does the compiler do to a struct,
which end of a word is the low byte. The header is compiled twice, from the same bytes: once
against glibc on Linux, and once against xv6's freestanding user library, which has no
`<stdint.h>`, no `size_t`, and no `<stddef.h>`.

```{literalinclude} ../sysfs/include/sysfs/probe.h
:language: c
:start-at: /* Byte order, asked of the machine
:end-before: /* Byte offset of a member
```

That constraint is why the header looks the way it does, and the comment at the top of it is
worth reading: it is the first example in the book of a design decision that exists entirely
because of where the code has to run.

Run it in both worlds:

```bash
make bench-xv6                                   # boots xv6, runs the probe, stamps the result
python3 -m pytest tests/test_xv6.py -q           # asserts the two targets agree
```

## What we measured

The xv6 target, described by a boot rather than by a claim:

```{include} _generated/ch00-xv6-environment.md
```

The C implementation it presents, as reported from inside the kernel:

```{include} _generated/ch00-probe-types.md
```

This is the **LP64** data model: `long` and pointers are 64-bit, `int` stays 32-bit, and every
scalar type's alignment equals its size. RISC-V spells its variant LP64D, for the
double-precision float ABI @riscv-psabi; AArch64 arrives at the same layout by its own route. If
you have only ever worked on 64-bit Linux this will look like the way things are. It is a choice
the ABI made — twice, independently — and [ch02](#ch02) takes it apart.

The third table is the one worth staring at. Two structs, the same three members, different
declaration order:

```{include} _generated/ch00-probe-layouts.md
```

The compiler did not reorder them — C forbids it — so writing them in the order that happened to
occur to you cost bytes that hold nothing at all. On one struct that is an oddity. Across an array
of a few million of them it is the difference between fitting in cache and not, which is
[ch15](#ch15)'s subject and the first place this chapter's dry table turns into a number of
nanoseconds.

And the reference machine's own account of itself:

```{include} _generated/ch00-board.md
```

## What this cannot tell you

Everything above is *structural*: sizes, offsets, byte order, which programs are in an image, how
many harts announced themselves. Those are questions QEMU answers perfectly, because they are
questions about what the instructions compute.

Not one of them is a question about time, and that is not an accident of what this chapter chose
to measure. It is the whole design. The xv6 target will never produce a timing in this book,
because a timing produced there would be meaningless, and a meaningless number in a table is
worse than a missing one — a missing number announces itself.

The reference machine's table above is the other half of the same discipline. If it is showing a warning box
rather than numbers, that is because the measurement has not been taken yet: nothing is estimated,
interpolated, or carried over from a different machine. `make bench-board` refuses to run
anywhere but the board, and `scripts/verify-numbers.py` rejects the result if it somehow arrives
from anywhere else.

Two more limits worth naming now, since both will come up repeatedly:

**A correct answer is not a fast answer.** CI compiles every `host`-target example for AArch64
and runs it under user-mode QEMU. That proves the instructions are right and the answers are
right, and it proves nothing whatsoever about cost. When a chapter says a result was checked in
CI, it means checked, not timed.

**This machine is one data point.** Four out-of-order cores with a three-level cache is an
ordinary shape, not a universal one. Ratios and mechanisms generalise; absolute numbers do not,
and the five chapters whose reading depends on this particular core say so in their own headers.

**And it is a machine that changes speed.** A Pi 5 throttles under sustained load, so a long run
can be measuring a different clock at the end than at the start. That is not a flaw in the board —
it is what most real hardware does, including the laptop you are reading this on, and a book that
measured on a machine which never throttled would be teaching you to ignore something that
matters. [ch14](#ch14) deals with it properly.

## Problems

Three, and each one has a test that passes only when you have solved it. There is no answer key
in the back of the book — which means there is no answer key to be wrong.

**0.1 — Which of these would you publish?**
`tests/ch00/problem_1_trust.py` asks you to write one function: given a stamped result, decide
whether a duration measured under those conditions is one this book may print. Five cases are
waiting for it, and exactly one of them is publishable. Getting this right is the same skill as
reading someone else's benchmark and noticing what they measured it on.

```bash
python3 -m pytest tests/ch00/test_problem_1_trust.py
```

**0.2 — Predict the padding.**
`tests/ch00/problem_2_abi.py` shows you a struct with five members and asks for its size, its
alignment, and the offset of each member — *before* you compile it. The test then compiles that
struct for whichever architecture this machine can execute, runs it, and tells you where you were
wrong. The tables above give you the sizes and alignments of the scalar types; the rest follows
from one rule — and it is the same rule on both architectures, which is the point.

**0.3 — Your first xv6 program.**
`tests/ch00/ch00ping.c` is a program that prints nothing. Make `ch00ping 41` print `pong 42`. The
arithmetic is not the exercise: the exercise is the path from a file in a test directory, through
the cross compiler, into xv6's user library, onto a file system image, into QEMU, and out of a
shell. If any link in that chain is missing you want to find out now, not in [ch06](#ch06).

```bash
python3 -m pytest tests/ch00 -q          # all three, including the ones you have not solved
```

Note that these tests are marked `problem` and CI deliberately does not run them. What CI does
run is the scaffolding beside each one: that the puzzle compiles, that the kernel boots with your
file staged into it, that the problem is answerable. The book is responsible for handing you a
problem that works. Making it pass is yours.

## Where to go next

The RISC-V specifications are the primary sources this book cites for anything architectural: the
unprivileged ISA @riscv-isa-unprivileged for instructions, the privileged architecture
@riscv-isa-privileged for CSRs, traps and paging, the ELF psABI @riscv-psabi for the calling
convention and the data model measured above, and the SBI specification @riscv-sbi for how Linux
reaches the counters. They are readable, and reading a specification directly is a skill this book
would like you to acquire early — the habit of checking rather than remembering is most of what
separates a confident answer from a correct one.

For the reference machine, Raspberry Pi's own documentation @rpi-bcm2712 gives the SoC and its
cache hierarchy, and Arm's Cortex-A76 technical reference manual @arm-a76-trm gives the pipeline
and the PMU events [ch17](#ch17) reads. The RISC-V hardware the preface argues against is
documented at @starfive-jh7110 and @sifive-u74 if you want to follow that thread. Either way the
caveat stands: where a document and a measurement disagree, the book prints the measurement and
says so.

The study behind that decision is @riscv-pmu-profiling, and it is worth reading even if you never
touch RISC-V — it is a good example of what it looks like to establish what a machine can actually
do, rather than what its documentation says it has.

The xv6 source @xv6-riscv-source is worth browsing before [ch01](#ch01), without trying to
understand it. Its authors also wrote a commentary on it, which is excellent and which this book
deliberately does not follow the structure of; if you want a second account of the same kernel
after Part II, that is the one to read.

[ch01](#ch01) takes a single program and follows it from source text to a result on both targets,
and asks — for the first of many times — which parts of that journey cost anything.
