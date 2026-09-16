---
title: "Prerequisites and Setup"
short_title: "00 · Prerequisites and Setup"
---

(prerequisites-and-setup)=
# 00 · Prerequisites and Setup

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` and `host` — every example says which |
| **Prerequisites** | none |
| **What it measures** | That both targets work, and exactly what they are: `bench/results/setup-xv6.json`, `bench/results/setup-host.json` |
| **What it captures** | What the compiler emits for each architecture: `bench/results/shapes-riscv64.json`, `bench/results/shapes-aarch64.json` — listings, not measurements |
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
about nine thousand lines, which you can stop mid-trap and inspect. Parts I, III and IV live there,
and
so does everything the book says about *what a program does*.

**`host`** is a small Linux machine on the desk, reached over SSH — a Raspberry Pi 5 in this book.
Everything about *what a program costs* is measured there, natively. [Part V](#part5) lives there.

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
The emulated targets run on any laptop and cover Parts I to IV. If the Pi has
not arrived yet, set up the xv6 half now and come back to the rest before [ch22](#the-same-program-on-both-targets). Nothing
in Parts I to IV depends on hardware you do not have.
:::

## What you need

Two machines, and only one of them has to be bought: whatever you are reading this on, which runs
both emulated targets, and a small Linux board for `host`. The reference is a **Raspberry Pi 5**,
and the requirement is a capability rather than a part number — `perf` has to both count and
sample, which [Appendix H](#appendix-h) states properly, along with how to check a machine you
already own and what changes if yours differs from the reference. Read it before you spend
anything. The rest of this chapter assumes the board is on your desk.

## Setting up the machine

A Pi is a well-trodden path and the Raspberry Pi documentation is the authority on it. What
follows is the shape of the task and the parts this book depends on.

**1. Write a 64-bit image.** Raspberry Pi OS (64-bit), written with Raspberry Pi Imager, which
will also set the hostname, your SSH key and your WiFi while it writes. Use its advanced options
— it saves the whole "find it on the network and change the default password" dance.

It has to be a **64-bit** image. A 32-bit userspace on ARMv7 does not get you the ARMv8 PMU, and
you would spend an afternoon finding that out.

It also has to be an image whose **device tree describes the PMU**, and that is a real choice
rather than a formality. The counters are in every Pi 5's silicon; whether Linux is told about
them depends on the `.dtb` your image ships. Reading the sources @rpi-dt-bcm2712: the Raspberry Pi
kernel carries an `arm-pmu` node for the Cortex-A76, with one overflow interrupt per core, and
every Pi 5 variant inherits it. Mainline Linux's own BCM2712 tree carries no such node at all.

So prefer an image built on the Raspberry Pi kernel, which is what Raspberry Pi OS and the
Raspberry Pi builds of other distributions use. A general-purpose distribution running a mainline
kernel with mainline device trees on the same board may have no hardware PMU exposed to it
whatever — not because the chip lacks one, but because nothing told the kernel it was there. One
command settles it either way, and it is the next section.

**2. Boot it, wired if you can.** Not because the link speed matters — nothing in [Part V](#part5) touches
the network, so bandwidth, latency and the grade of cable are all irrelevant to every number in
this book. What a radio does is make the machine do work you did not ask for: its driver takes
interrupts and runs softirqs on the same cores your benchmark is running on, and a lossy link adds
`sshd` wakeups on top. [ch27](#memory-ordering-on-real-hardware) and [ch28](#the-os-layers-cost), which measure small per-operation costs,
are where that is most likely to show.

Most likely, and not measured. This book has not put a number on it, which means you should treat
the advice as hygiene rather than as a result — and [ch23](#measuring) will hand you the tools to
settle it yourself, because "the same benchmark, one thing changed that should not matter" is
exactly that chapter's subject. Run it both ways and find out whether you can tell.

Only the machine being measured needs the cable. Your laptop can stay on Wi-Fi: its radio
interrupts its own cores, not the ones running the benchmark. So for most people this costs a
cable to the nearest router or switch port and nothing else — the machine gets an address and a
route without being asked, and both ends are on the same network, so everything below works.

If no router port is within reach, a cable straight into a laptop's Ethernet port — a dock's,
usually, or a cheap USB-C adapter — works too, and is arguably quieter, since nothing else on a
two-host link is broadcasting at it. But that link has
no DHCP server and no route out, so the machine comes up with a link-local address and no
internet, and the first `apt install` fails in a way that looks like a broken image. Turn on your
laptop's internet sharing (macOS: Settings → General → Sharing → Internet Sharing, from Wi-Fi to
the Ethernet adapter; Linux: set the connection to *Shared to other computers*) and both problems
go away at once — it hands out the lease and routes the traffic. `.local` names resolve over a
direct cable either way, so step 3 works unchanged.

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

This is the one capability [Part V](#part5) cannot work around, and it is worth being suspicious about,
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

If nothing is counted, the usual cause on ARM is the missing device-tree node described above.
Ask the kernel directly:

```bash
dmesg | grep -i perfevents
ls /sys/bus/event_source/devices/
```

A machine whose PMU registered says so at boot, naming the driver it bound:

```text
hw perfevents: enabled with armv8_cortex_a76 PMU driver, 7 counters available
```

and `/sys/bus/event_source/devices/` contains a matching entry. No such line, or no such entry,
and no amount of care in `perf`'s arguments will help: there is nothing underneath it. On a RISC-V
machine the failure is usually further down — the counters are machine-mode CSRs reached through
the firmware's SBI PMU extension @riscv-sbi, so check for `CONFIG_RISCV_PMU_SBI` and a firmware
that provides it.

Until `perf stat` prints real counts, [Part V](#part5) cannot start, and no amount of care in the chapters
substitutes for it.

### Counting is not sampling

There is a second capability, and it is the reason this book's `host` target is an ARM machine.

`perf stat` **counts**: it totals events over a whole run. `perf record` **samples**: it
interrupts the program thousands of times a second to ask where it is, and builds a picture of
where the time went from those interruptions. Sampling needs the counters to raise an interrupt
when they overflow, and that is a separate hardware feature from counting.

Test it with a program that is actually running. This matters more than it looks:

```bash
perf record -F 999 -e cycles -o /tmp/perf.data -- sleep 2    # proves nothing
perf report --stats -i /tmp/perf.data | grep SAMPLE
```

A sleeping process is off the CPU, so it retires no instructions and burns no cycles, and a
perfectly working PMU returns almost nothing. The command succeeds, the sample count is near
zero, and you have learned nothing about the machine. Give it something to sample instead:

```bash
perf record -F 999 -e cycles -o /tmp/perf.data -- \
    python3 -c 'x = 0
for _ in range(4_000_000): x += 1'
perf report --stats -i /tmp/perf.data | grep SAMPLE
```

Now the sample count is the answer, and `bench/run_setup.py` asks exactly this question the same
way — because the first version of it ran `perf record -- true`, believed the zero exit status,
and would have declared a board capable of something it had never been asked to do:

```{literalinclude} ../bench/run_setup.py
:language: python
:start-at: def perf_can_sample
:end-before:     if not shutil.which("perf")
```

An exit status is not evidence. It is the same mistake as believing a counter that reads zero,
and it is worth meeting twice in one chapter.

On ARM, overflow interrupts are a standard PMU feature. On RISC-V they are the **Sscofpmf**
extension @riscv-sscofpmf, and a kernel on a core without it says so at boot and then declines:

```text
riscv-pmu-sbi: Perf sampling/filtering is not supported as sscof extension is not available
```

[ch29](#whole-machine-profiling) is entirely about sampling, so on a machine that cannot do it that chapter has
nothing to measure. `verify-setup.py` reports the two capabilities separately, precisely so you
find out now rather than three hundred pages in.

The distinction generalises well beyond RISC-V, which is why it is worth learning here: a
profiler that samples is answering a different question, with different failure modes, from a
counter that totals. [ch23](#measuring) takes that apart properly and [ch29](#whole-machine-profiling) depends on it.

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
example in [Part V](#part5) can be compiled and **checked for correctness** away from the board. It
cannot tell you anything about time, and the repository does not let it try — but it is the
difference between being able to work on [Part V](#part5) from a train and not.

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

**Getting out again is `Ctrl-A` then `X`.** It is a sequence rather than a chord: hold control and
press A, let both go, then press X. QEMU exits immediately.

That it is QEMU's key and not xv6's is the point. xv6 has no way to halt the machine — no
`shutdown`, no `halt`, nothing — so there is nothing to type at the shell prompt that would end
the session. You are stopping the emulator out from under a kernel that has no opinion about it,
which is the first of many small reminders that this is a teaching kernel and not a product.

`Ctrl-A` then `C` switches the same terminal to QEMU's own monitor, where `quit` also exits and
`info registers` works without a debugger attached. `Ctrl-A` then `C` again switches back. This is
worth knowing before you need it: when [Appendix B](#appendix-b) has QEMU halted at reset waiting
for a debugger, the terminal looks frozen, and the monitor is how you confirm it is not.

The same thing non-interactively, which is how the tests do it:

```bash
python3 scripts/xv6-run.py -c ls -c sysprobe
```

## Running the book's programs

Every listing in this book is a real file that really compiles, and `./run` builds and runs any of
them on whichever machine it belongs to.

```bash
./run --list
```

```bash
./run firstc          # a host program: compiled and run here
./run trap            # bare metal: cross-compiled and booted with no operating system
./run sysprobe --target xv6
```

Use it constantly. Change a line in the source, run it again, see what moved — that loop is what
this book is asking you to do, and it is the difference between reading that a handler must
advance `mepc` and watching what happens when it does not.

`./run` never touches anything committed. The figures in the chapters come from `bench/run_*.py`,
which stamp a result and refuse one that has stopped demonstrating its chapter's claim; `./run`
just builds and runs, so experimenting is free and cannot corrupt a number.

## Checking the whole thing

```bash
python3 scripts/verify-setup.py
```

It reports each target separately, because most machines can run one of them. On a laptop it
confirms the cross compiler, QEMU, the submodule and a usable debugger, then explains that the
`host` target is read-only here and says whether a cross-built correctness path is available. On
the machine itself it reads the device tree and `/proc/cpuinfo`, prints whatever that kernel says
identifies the core — an implementer and part number on ARM, an ISA string and three
implementation IDs on RISC-V — and checks that `perf` reaches hardware.

Notice what it does *not* do: look anything up. Every fact it prints is read from the machine in
front of it. A specification describes a product line; `/proc/cpuinfo` describes the silicon that
is about to produce your numbers, and when the two disagree — which happens — the book cites the
one it measured.

### The same program in both worlds

Two checks remain, and they are the interesting ones. The first produces this chapter's first real
result.

`sysfs/include/sysfs/probe.h` asks the machine a handful of questions it can answer without a
library: how big is each scalar type, where may it start, what does the compiler do to a struct,
which end of a word is the low byte. It is compiled twice from the same bytes, for two targets
that disagree about what a C library is, and it says so itself — the first design decision in this
book that exists entirely because of where the code has to run:

```{literalinclude} ../sysfs/include/sysfs/probe.h
:language: c
:start-at: /* Facts the machine will tell you
:end-before: #ifndef SYSFS_PROBE_H
```

Everything else about the header follows from that. Asking the machine which end of a word it puts
the low byte at, rather than assuming, costs three instructions:

```{literalinclude} ../sysfs/include/sysfs/probe.h
:language: c
:start-at: /* Byte order, asked of the machine
:end-before: /* Byte offset of a member
```

Run it in both worlds:

```bash
make bench-xv6                                   # boots xv6, runs the probe, stamps the result
python3 -m pytest tests/test_xv6.py -q           # asserts the two targets agree
```

## What we measured

The xv6 target, described by a boot rather than by a claim:

```{include} _generated/prerequisites-and-setup-xv6-environment.md
```

The C implementation it presents, as reported from inside the kernel:

```{include} _generated/prerequisites-and-setup-probe-types.md
```

This is the **LP64** data model: `long` and pointers are 64-bit, `int` stays 32-bit, and every
scalar type's alignment equals its size. RISC-V spells its variant LP64D, for the
double-precision float ABI @riscv-psabi; AArch64 arrives at the same layout by its own route. If
you have only ever worked on 64-bit Linux this will look like the way things are. It is a choice
the ABI made — twice, independently — and [ch12](#representing-information) takes it apart.

The third table is the one worth staring at. Two structs, the same three members, different
declaration order:

```{include} _generated/prerequisites-and-setup-probe-layouts.md
```

The compiler did not reorder them — C forbids it — so writing them in the order that happened to
occur to you cost bytes that hold nothing at all. On one struct that is an oddity. Across an array
of a few million of them it is the difference between fitting in cache and not, which is
[ch24](#the-memory-hierarchy)'s subject and the first place this chapter's dry table turns into a number of
nanoseconds.

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
matters. [ch23](#measuring) deals with it properly.

## Problems

Three, and each one has a test that passes only when you have solved it. There is no answer key
in the back of the book — which means there is no answer key to be wrong.

**0.1 — Which of these would you publish?**
`tests/prerequisites_and_setup/problem_1_trust.py` asks you to write one function: given a stamped result, decide
whether a duration measured under those conditions is one this book may print. Five cases are
waiting for it, and exactly one of them is publishable. Getting this right is the same skill as
reading someone else's benchmark and noticing what they measured it on.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_1_trust.py
```

**0.2 — Predict the padding.**
`tests/prerequisites_and_setup/problem_2_abi.py` shows you a struct with five members and asks for its size, its
alignment, and the offset of each member — *before* you compile it. The test then compiles that
struct for whichever architecture this machine can execute, runs it, and tells you where you were
wrong. The tables above give you the sizes and alignments of the scalar types; the rest follows
from one rule — and it is the same rule on both architectures, which is the point.

**0.3 — Your first xv6 program.**
`tests/prerequisites_and_setup/ch00ping.c` is a program that prints nothing. Make `ch00ping 41` print `pong 42`. The
arithmetic is not the exercise: the exercise is the path from a file in a test directory, through
the cross compiler, into xv6's user library, onto a file system image, into QEMU, and out of a
shell. If any link in that chain is missing you want to find out now, not in [ch15](#traps-and-system-calls).

```bash
python3 -m pytest tests/prerequisites_and_setup -q          # all three, including the ones you have not solved
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
and the PMU events [ch26](#the-cpu) reads. The RISC-V hardware the preface argues against is
documented at @starfive-jh7110 and @sifive-u74 if you want to follow that thread. Either way the
caveat stands: where a document and a measurement disagree, the book prints the measurement and
says so.

The study behind that decision is @riscv-pmu-profiling, and it is worth reading even if you never
touch RISC-V — it is a good example of what it looks like to establish what a machine can actually
do, rather than what its documentation says it has.

The xv6 source @xv6-riscv-source is worth browsing before [ch11](#what-a-computer-does-with-a-program), without trying to
understand it. Its authors also wrote a commentary on it, which is excellent and which this book
deliberately does not follow the structure of; if you want a second account of the same kernel
after [Part IV](#part4), that is the one to read.

[ch11](#what-a-computer-does-with-a-program) takes a single program and follows it from source text to a result on both targets,
and asks — for the first of many times — which parts of that journey cost anything.
