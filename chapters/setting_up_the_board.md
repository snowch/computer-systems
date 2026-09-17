---
title: "Setting Up the Board"
short_title: "01 · Setting Up the Board"
---

(setting-up-the-board)=
# 01 · Setting Up the Board

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — Linux on real hardware, natively, over SSH |
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **Assumes** | A Linux board whose `perf` can both count and sample |
| **What it measures** | What the board says about itself once it is working: `bench/results/setup-host.json` |
:::

## The question

**Is this machine telling me the truth about itself?**

[ch00](#prerequisites-and-setup) got the emulated targets working, and they are enough for
everything up to [Part V](#part5). This chapter sets up the other machine: the one every number in
the book is measured on, and therefore the one whose word has to be good.

A counter can be present, be readable, return a number, and still be a software estimate rather
than a count of anything. Most of this chapter is spent establishing that
the machine in front of you is not doing that, because a figure produced by a fake counter is
indistinguishable from a real one once it is in a table.

[Appendix H](#appendix-h) covers the decision that comes first — what the board has to be able to
do, and how to tell whether the one you own qualifies. This chapter assumes it is on your desk.

## The material

A Pi is a well-trodden path and the Raspberry Pi documentation is the authority on it. What
follows is the shape of the task and the parts this book depends on.

**1. Write a 64-bit image.** Raspberry Pi OS (64-bit), written with Raspberry Pi Imager, which
will also set the hostname, your SSH key and your Wi-Fi while it writes. Use its advanced options
— it saves the whole "find it on the network and change the default password" dance.

It has to be a **64-bit** image. A 32-bit userspace on ARMv7 does not get you the ARMv8 PMU, and
you would spend an afternoon finding that out.

It also has to be an image whose **device tree describes the PMU**, and not every image does. The
counters are in every Pi 5's silicon; whether Linux is told about them depends on the `.dtb` your
image ships. In the sources @rpi-dt-bcm2712, the Raspberry Pi kernel carries an `arm-pmu` node for
the Cortex-A76, with one overflow interrupt per core, and every Pi 5 variant inherits it. Mainline
Linux's own BCM2712 tree carries no such node at all.

So prefer an image built on the Raspberry Pi kernel, which is what Raspberry Pi OS and the
Raspberry Pi builds of other distributions use. A general-purpose distribution running a mainline
kernel with mainline device trees on the same board may have no hardware PMU exposed to it
whatever — not because the chip lacks one, but because nothing told the kernel it was there. One
command settles it either way, and it is the next section.

**2. Boot it, wired if you can.** A radio makes the machine do work you did not ask for: its
driver takes interrupts and runs softirqs on the same cores your benchmark is running on, and a
lossy link adds `sshd` wakeups on top. Link speed has nothing to do with it — nothing in
[Part V](#part5) touches the network, so bandwidth, latency and the grade of cable are all
irrelevant to every number in this book. [ch28](#memory-ordering-on-real-hardware) and [ch29](#the-os-layers-cost), which measure small per-operation costs,
are where the interference is most likely to show.

That is a prediction, not a measurement. This book has not put a number on it, so treat the advice
as hygiene rather than as a result — and [ch24](#measuring) will hand you the tools to settle it
yourself, because "the same benchmark, one thing changed that should not matter" is exactly that
chapter's subject. Run it both ways and find out whether you can tell.

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

Counting is the one capability [Part V](#part5) cannot work around, and `perf` reports a failure
to reach hardware in a way that is easy to skim past. So be suspicious of it.

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

Until `perf stat` prints real counts, [Part V](#part5) cannot start, and nothing in the later chapters
substitutes for it.

### Counting is not sampling

There is a second capability, sampling, and it is the reason this book's `host` target is an ARM
machine.

`perf stat` **counts**: it totals events over a whole run. `perf record` **samples**: it
interrupts the program thousands of times a second to ask where it is, and builds a picture of
where the time went from those interruptions. Sampling needs the counters to raise an interrupt
when they overflow, and that is a separate hardware feature from counting.

Test it with a program that is actually running. The first of these commands looks like a test and
is not:

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

[ch30](#whole-machine-profiling) is entirely about sampling, so on a machine that cannot do it that chapter has
nothing to measure. `verify-setup.py` reports the two capabilities separately, precisely so you
find out now rather than three hundred pages in.

A profiler that samples answers a different question from a counter that totals, and it fails in
different ways. That distinction generalises well beyond RISC-V. [ch24](#measuring) takes it
apart properly and [ch30](#whole-machine-profiling) depends on it.

## What we measured

The board's own account of itself, taken on the board: what it is, what its counters do, and
whether `perf` can both count and sample. Every figure in [Part V](#part5) is measured on the
machine this describes, which is why it is recorded rather than assumed.

```{include} _generated/setting-up-the-board-report.md
```

## What this cannot tell you

**Whether your numbers will match the book's.** They will not, exactly, and they are not meant
to. The committed figures came from one board with one kernel and one firmware; yours differs in
at least the last two. What should match is the *shape* — which of two things is faster, and by
roughly how much — and where it does not, the chapter that prints the figure says what it
depended on.

**Whether a counter counts what its name says.** `perf` reports the name the kernel gives an
event, and the kernel takes that from a table it was told. This chapter establishes that counting
and sampling work at all; whether a given event means what you think is a question for
[Appendix C](#appendix-c), which is generated from the board rather than written.

**Anything about the board under load.** Everything here is a single quiet measurement on an idle
machine. Thermal throttling, a busy neighbour and a governor that changes frequency mid-run are
all real, all capable of moving a number more than the thing being measured, and all
[ch24](#measuring)'s subject.

## Problems

Two, in `tests/setting_up_the_board/`. Both are Python stubs: this chapter comes before any C.

**1.1 — Is this counter real?**
Six `perf stat` outcomes. Say which of them are counts of something the hardware did, and which
are the kernel estimating or declining.

```bash
python3 -m pytest tests/setting_up_the_board/test_problem_1_counters.py
```

**1.2 — Can this machine sample?**
Counting and sampling are different capabilities and a machine can have the first without the
second. Given what a machine reports, say which of the book's parts it can finish.

```bash
python3 -m pytest tests/setting_up_the_board/test_problem_2_sampling.py
```

## Where to go next

[Appendix H](#appendix-h) states the requirements this chapter assumes, and `hardware/README.md`
is the same thing as a checklist. The counter-overflow interrupt that sampling needs is the
Sscofpmf extension @riscv-sscofpmf on RISC-V and a standard part of the PMU on ARM; the reference
board's SoC is documented by its vendor @rpi-bcm2712.
