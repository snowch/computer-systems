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

## Two targets, and why it has to be two

```{figure} _figures/ch00-targets.svg
:alt: The xv6 and host targets side by side, with what each can and cannot answer.
:width: 100%

The division of labour. Every chapter declares which target it uses, and every figure records
which one produced it.
```

**`xv6`** is the MIT teaching kernel, running under `qemu-system-riscv64`. It is a complete
operating system — processes, page tables, traps, a file system with a write-ahead log — in about
nine thousand lines. You can stop the whole machine in the middle of a trap and print a page
table. Parts I and II live here, and so does everything the book says about *what a program does*.

**`host`** is a RISC-V single-board computer on the desk: a StarFive VisionFive 2 Lite, running
Ubuntu, reached over SSH. Everything the book says about *what a program costs* is measured
there, natively. Part III lives here.

The split is the book's central argument rather than a convenience. QEMU is a functional
emulator: it computes what the instructions compute, and it models nothing else. There is no
cache in it, no branch predictor, no store buffer, no pipeline, no memory latency. Ask it how
long a loop took and it will answer, and the answer will describe the laptop QEMU was running on
and the translation strategy it happened to pick — not the RISC-V machine you think you are
studying.

This is not a limitation to work around. It is a fact worth internalising early, because it
generalises: almost every convenient way to observe a program changes what you are observing. A
debugger stops it. A profiler samples it. A print statement in a loop makes the loop something
else. The discipline this book is really teaching is knowing which of your tools is lying to you
about which question.

So the repository enforces the split rather than trusting anyone to remember it. Every result
file records where it was measured, and `scripts/verify-numbers.py` rejects two things outright:
a `host` figure that was not produced natively on RISC-V hardware, and an `xv6` result that
contains a duration at all.

```{literalinclude} ../bench/stamp.py
:language: python
:start-at: def provenance_problems
:end-before:     problems: list[str] = []
```

:::{note} You can start with one target
The xv6 target runs on any laptop and covers Parts I and II — fourteen chapters. If the board has
not arrived yet, set up the xv6 half now and come back to the rest before
[ch13](#ch13). Nothing in Parts I and II depends on hardware you do not have.
:::

## What to buy

Not a specific board — a board that can do four things. That distinction matters more than it
looks, so it is worth a paragraph before the shopping list.

This book originally named one model. While chapter 0 was being written, the retailer listing for
it went out of stock, and the exact variant named turned out to be difficult to buy in the UK at
all. A book outlives a product listing; one that hard-codes a part number has a broken first
chapter within a year, and the reader who hits it cannot tell whether the substitute they found is
equivalent.

So here is what the machine has to be able to do:

| | Requirement | Why |
|---|---|---|
| **Must** | RV64GC (`rv64imafdc`) application processor running Linux, reachable over SSH | The instruction set you read in a debugger in Part I is the one you count in Part III, with no translation in your head |
| **Must** | `perf stat -e cycles,instructions -- true` returns real counts | **The one requirement with no workaround.** Part III does not exist without it |
| **Must** | 4 GB RAM (8 GB preferred); 2 cores (4 or more preferred) | [ch18](#ch18) measures what cores cost each other, which needs more than two |
| **Prefer** | An in-order core — the SiFive U74 family or similar | The reason is below, and it is the one that changes how the book reads |
| **Prefer** | Still in production, still receiving distro images | An abandoned vendor kernel is where `perf` support goes to die |
| **Nice** | M.2 NVMe | Builds and [ch12](#ch12) are far less tedious |
| **Nice** | RVV 1.0 vector support | [ch21](#ch21) reasons about vectorisation because the reference hardware cannot do it. Yours might |
| **Nice** | 3.3 V UART header | For watching a boot that never reaches the network |

Plus the unglamorous parts: a **USB-C power supply** rated for the board — underpowering one
produces instability that reads exactly like a kernel bug — a **microSD card** of 32 GB or more
that is not the cheapest on the shelf, and an **Ethernet cable**, because WiFi works but wired is
one fewer variable when a measurement looks strange.

You also need a development machine. The book assumes a Mac, but anything that runs Homebrew or
apt and holds an SSH key will do. It never measures anything.

### The requirement to be suspicious about

The counters. Everything else on that list is printed on the box; whether `perf` can read the
hardware is not, and it is the one that stops the book dead.

On RISC-V the performance counters are not reached directly by Linux. The hardware exposes them
as machine-mode CSRs, the kernel runs in supervisor mode, and the two are bridged by the firmware
through the **SBI PMU extension** @riscv-sbi. So whether `perf stat` works is a property of the
software image as much as of the silicon — and a datasheet saying the core has a hardware
performance monitor tells you nothing about whether a shipping distro will let you read it.

Which is why the book's answer to "will this board work?" is a script rather than a claim, and
why it runs on the board after it arrives rather than on a specification before it.

### Finding one

The requirements above are stable. Which boards satisfy them, in your country, at the price you
want, on the day you read this — is not, and this book is the wrong place to answer it.

So `hardware/find-a-board.txt` states those requirements in a form something else can shop
against. Paste it into an assistant that can search the web, with your country and budget filled
in:

```{literalinclude} ../hardware/find-a-board.txt
:language: text
:start-at: HARD REQUIREMENTS
:end-before: STRONGLY PREFERRED
```

That is an extract; the file also covers what is merely preferred, and asks for a **source** for
the `perf` claim specifically, because that is the claim most likely to come back confidently
wrong. Treat the reply as a shortlist rather than an answer — and note that the verification step
does not depend on it being right.

:::{caution} The purchase is yours
This book does not sell hardware, has not tested most of what a search might surface, and has no
relationship with any vendor. Availability and prices change, listings go out of stock, and an
assistant will occasionally state a board's `perf` support with more confidence than its evidence
supports. Verify the retailer, the price and the return policy yourself; nothing here is a
warranty that a given board will work for you.

The practical version: the requirement you cannot check before it arrives is the one that matters
most. Buy somewhere that takes returns, and run `scripts/verify-setup.py` on day one rather than
the week you reach Part III.
:::

### Why an in-order core

Two reasons this book cares, and the second is the real one.

RISC-V, so Part I and Part III are about the same instruction set.

And **in-order** — a short pipeline, no out-of-order execution, no register renaming. On a modern
out-of-order core, the connection between an instruction you wrote and a cycle that got spent is
mediated by so much machinery that small experiments frequently come out backwards. On an
in-order core, a dependent load that misses in cache stalls, visibly, for as long as the miss
takes. Part III's measurements are *legible* in a way the same measurements on a laptop are not —
and once you have seen a mechanism clearly on a simple machine, you know what to go looking for
on a complicated one.

An out-of-order RISC-V board is not disqualifying. It will make [ch17](#ch17) and [ch18](#ch18)
harder to read, and your numbers will differ more from the committed ones. Everything still works.

### The reference machine, and why your numbers will differ

Every figure in Part III of this repository was measured on a **StarFive VisionFive 2 Lite**
(JH7110S, four SiFive U74 cores) unless the result says otherwise — and every result does say,
because each one stamps the board model, ISA string and core IDs of the machine that produced it.

So your numbers will not match, and that is expected rather than a problem. The book is about
ratios, mechanisms and method, and those transfer.

### Which chapters actually depend on the hardware

Most do not. Four do, and rather than let you discover that two hundred pages in, here they are
up front. Each of these says the same thing in its own header, so you cannot open one without
being told.

| Chapter | What it assumes | What changes on a different board |
|---|---|---|
| [ch15](#ch15) | A particular cache hierarchy — levels, sizes, line size, TLB reach | The numbers, entirely. The method is the chapter, and measuring *your own* hierarchy is the exercise |
| [ch17](#ch17) | An in-order pipeline, and the PMU events this core exposes | The experiments still run. On an out-of-order core the results are harder to attribute, and some come out backwards |
| [ch18](#ch18) | Four cores, and this interconnect's coherence behaviour | A different core count moves the scaling curve without changing the mechanism. Two cores make the chapter thin |
| [ch21](#ch21) | **No vector unit** | The one assumption a better board invalidates in your favour: with RVV 1.0 you can measure what this chapter only reasons about |

The pattern is worth noticing, because it is the same one the two targets follow. A chapter's
*mechanism* survives a change of hardware; its *numbers* do not. That is why the book insists on
stamping every figure with the machine that produced it, and why [ch15](#ch15) is written as an
instruction rather than a table — a cache hierarchy you measured is worth more than one you read.

If none of your numbers resemble the committed ones and you want to know whether that is your
board or your method: it is almost always your board, and [ch14](#ch14) is where you learn to
tell the difference.

`hardware/README.md` has the requirements, the prompt and the verification step in one place, for
when you are standing in front of a shop rather than reading a chapter.

## Setting up the board

The vendor's documentation is the authority on flashing and first boot, and it changes as images
are released @starfive-jh7110. What follows is the shape of the task and the parts that are
generic; when the two disagree, believe the vendor and write down what you actually did.

**1. Write an image to the microSD card.** Download the current Debian or Ubuntu image for the
board. On the Mac, `diskutil list` tells you which device the card is, and then:

```bash
diskutil unmountDisk /dev/diskN
sudo dd if=<image>.img of=/dev/rdiskN bs=4m status=progress
sync
```

Check the device name twice. `dd` will write to your internal disk just as happily.

**2. Set the boot source.** The VisionFive 2 boards have small switches that select where
firmware looks for a bootloader. Set them for the microSD slot as the vendor's quick-start
describes, insert the card, connect Ethernet, then power up.

**3. Find it on the network.** If it took a DHCP lease, your router will show it; otherwise a
serial console over the UART adapter shows the boot log and lets you log in directly. Then:

```bash
ssh-copy-id user@visionfive          # replace with the board's user and address
ssh user@visionfive
```

Change the default password before doing anything else. A board on your LAN with vendor default
credentials is a board somebody else can also use.

**4. Give it a name.** Add it to `~/.ssh/config` on the Mac:

```
Host vf2
    HostName 192.168.1.50
    User user
    ServerAliveInterval 30
```

Now `ssh vf2` works, `make bench-board` over SSH works, and VS Code's Remote-SSH extension can
open the board as a workspace — *Remote-SSH: Connect to Host…*, pick `vf2`, and the editor runs
its file operations and its terminal on the board while the interface stays on the Mac. That is
the arrangement the rest of the book assumes: you edit on the Mac, and everything that touches a
counter happens on the board.

### The toolchain on the board

```bash
sudo apt update
sudo apt install -y build-essential gdb git python3 python3-pip linux-tools-common
```

`perf` is the awkward one. It ships as part of the kernel's tooling, so the package that provides
it is tied to the running kernel version, and on RISC-V distributions it is not always packaged
at all. Try, in order:

```bash
sudo apt install -y "linux-tools-$(uname -r)"    # the matching package, if it exists
sudo apt install -y linux-tools-generic          # a close-enough build
perf --version
```

If neither works, build it from the kernel source tree — `make -C tools/perf` — against the
source matching `uname -r`. A `perf` built for a different kernel will run and will quietly fail
to open some events, which is the worst of the available outcomes.

### Proving the counters are real

This is the one capability Part III cannot work around, and it is worth being suspicious about,
because `perf` reports a failure to reach hardware in a way that is easy to skim past.

On RISC-V, the performance counters are not reached directly by Linux. The hardware exposes them
as machine-mode CSRs, and the kernel — which runs in supervisor mode — asks the firmware for them
through the **SBI PMU extension** @riscv-sbi. So whether `perf stat` works on this board depends
on the firmware as much as on the silicon: the core has the counters, and OpenSBI decides whether
you may read them.

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

If the counters are not available, check that the running kernel has `CONFIG_RISCV_PMU_SBI`
enabled and that the firmware provides the PMU extension. Until `perf stat` prints real counts,
Part III cannot start — and no amount of care in the chapters can substitute for it.

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

This is the **LP64D** data model: `long` and pointers are 64-bit, `int` stays 32-bit, and every
scalar type's alignment equals its size @riscv-psabi. If you have only ever worked on 64-bit
Linux this will look like the way things are; it is a choice the ABI made, and [ch02](#ch02)
takes it apart.

The third table is the one worth staring at. Two structs, the same three members, different
declaration order:

```{include} _generated/ch00-probe-layouts.md
```

The compiler did not reorder them — C forbids it — so writing them in the order that happened to
occur to you cost bytes that hold nothing at all. On one struct that is an oddity. Across an array
of a few million of them it is the difference between fitting in cache and not, which is
[ch15](#ch15)'s subject and the first place this chapter's dry table turns into a number of
nanoseconds.

And the board's own account of itself:

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

The board's table above is the other half of the same discipline. If it is showing a warning box
rather than numbers, that is because the measurement has not been taken yet: nothing is estimated,
interpolated, or carried over from a different machine. `make bench-board` refuses to run
anywhere but the board, and `scripts/verify-numbers.py` rejects the result if it somehow arrives
from anywhere else.

Two more limits worth naming now, since both will come up repeatedly:

**A correct answer is not a fast answer.** CI compiles every `host`-target example for RV64 and
runs it under user-mode QEMU. That proves the instructions are right and the answers are right,
and it proves nothing whatsoever about cost. When a chapter says a result was checked in CI, it
means checked, not timed.

**This board is one data point.** Four in-order cores at a modest clock is a deliberately simple
machine, chosen because its behaviour is legible. Ratios and mechanisms generalise; absolute
numbers do not, and a chapter that expects a result to be specific to this core says so.

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
struct for RISC-V, runs it, and tells you where you were wrong. The tables above give you the
sizes and alignments of the scalar types; the rest follows from one rule.

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

For the board and its core, the vendor documentation @starfive-jh7110 and SiFive's core complex
manual @sifive-u74 are the references, with the caveat this chapter has already made: where they
and a measurement disagree, the book prints the measurement and says so.

The xv6 source @xv6-riscv-source is worth browsing before [ch01](#ch01), without trying to
understand it. Its authors also wrote a commentary on it, which is excellent and which this book
deliberately does not follow the structure of; if you want a second account of the same kernel
after Part II, that is the one to read.

[ch01](#ch01) takes a single program and follows it from source text to a result on both targets,
and asks — for the first of many times — which parts of that journey cost anything.
