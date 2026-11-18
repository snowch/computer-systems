---
title: "01 · Setting Up the Board"
short_title: "01 · Setting Up the Board"
---

(setting-up-the-board)=
# 01 · Setting Up the Board

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `host` — Linux on real hardware, natively, over SSH |
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **Assumes** | A Linux board whose `perf` can both count and sample |
| **Evidence** | Machine details and whether `perf` can count events and sample where they occur. |
:::

## The question

Can your native Linux machine count hardware events and sample where they occur?

A hardware performance counter records processor events such as cycles and retired instructions.
Counting and sampling use different capabilities. Check both on the machine that will run the
performance experiments. The recorded table below shows what those checks returned on the
reference board.

(setting-up-the-board-example)=
## Set up the board and check its counters

### Connect to the board

[Appendix H](#appendix-h) describes the board requirements. If you are setting up a Raspberry
Pi, select Raspberry Pi OS (64-bit) in Raspberry Pi Imager and configure the hostname, user and
SSH key before you write the image. Boot the board. Use Ethernet if available, so the board's
Wi-Fi driver contributes less activity during measurements.

From your computer, connect with SSH using the hostname and user you configured. For example,
if you chose host name `raspberrypi` and user `bench`, run:

```bash
ssh bench@raspberrypi.local
```

Once the shell opens, the following commands run on the board. You can also use a terminal
attached to the board.

### Install the native tools

On Raspberry Pi OS, run:

```bash
sudo apt update
sudo apt install -y build-essential git python3-venv linux-perf
perf --version
```

On Ubuntu, use the package that supplies `perf` for the running kernel, such as
`linux-tools-$(uname -r)` or `linux-tools-raspi`. Check `uname -m` for `aarch64` on a 64-bit Pi.

Use [ch00](#prerequisites-and-setup) to create a checkout and Python environment on the board.
Install the RISC-V cross tools there only if you intend to run the emulated examples there too.
Run the following checks in the board's terminal.

(proving-the-counters-are-real)=
### Check hardware event counts

```bash
perf stat -e cycles,instructions -- true
```

Find the lines labelled `cycles` and `instructions`. Both should show positive hardware counts.
If `perf` reports `<not supported>`, `<not counted>`, zero, or a permission error, it has not
established that both counters work. Check the error text before interpreting the figures.

:::{note} Troubleshoot missing hardware counters
:class: dropdown

The *device tree* tells the Linux kernel what hardware is available. On a Pi, look for the
processor's *performance monitoring unit* (PMU) in the boot messages and event source devices:

```{code-block} bash
sudo dmesg | grep -i perfevents
ls /sys/bus/event_source/devices/
```

On the reference Pi, the kernel announces an `armv8_cortex_a76` driver. Whether Linux exposes that
PMU depends on the device tree supplied with the image @rpi-dt-bcm2712. On RISC-V, the firmware
must provide the SBI PMU interface @riscv-sbi and the kernel must include
`CONFIG_RISCV_PMU_SBI`. [Appendix H](#appendix-h) explains why two images can report different
counter availability on the same hardware.
:::

(counting-is-not-sampling)=
### Check hardware event sampling

`perf stat` reports event totals over a run. `perf record` collects samples, which record where
execution was when a configured counter triggered a sample. Use a workload that runs on the CPU
so the recorder has activity to sample:

```bash
recording=$(mktemp)
perf record -F 999 -e cycles -o "$recording" -- \
    python3 -c 'x = 0
for _ in range(4_000_000): x += 1'
perf report --stats -i "$recording" | grep SAMPLE
```

Check for a positive **SAMPLE events** count. A successful command with no samples leaves the
sampling capability unchecked. The counter needs to interrupt the processor when it overflows.
On RISC-V that capability is provided by the Sscofpmf extension @riscv-sscofpmf.

From the board checkout, run `python3 scripts/verify-setup.py` to see the two checks summarised.
If it can count but cannot sample, you can still use the counting examples. Read
[ch30](#whole-machine-profiling)'s recorded runs for the examples that need samples.

## What we measured

This is the saved setup report for the reference board. Compare **Kernel**, **Cores online**,
**perf stat reads hardware counters**, and **Samples collected in the capability check** with
your machine. Which parts of the setup can you reproduce, and which depend on the board?

```{include} _generated/setting-up-the-board-report.md
```

## What this cannot tell you

The setup checks establish that these events can count and sample under the test conditions.
[Appendix C](#appendix-c) describes the reference board's event names and multiplexing. Interpret
a specific event using the processor and kernel documentation for your machine.

The checks do not establish how a workload will behave under sustained load. Frequency changes,
interrupts and competing processes can change a timing. [ch24](#measuring) shows how to record
those conditions and compare runs.

## Problems

Use the files below in your local checkout. Run each test command from the repository root.

**1.1 — Is this counter real?**
Open `tests/setting_up_the_board/problem_1_counters.py`. Complete `counts_hardware_events`.
Decide which `perf stat` reports contain actual hardware counts. The test gives a report for
each case, including estimated and unsupported events.

```bash
python3 -m pytest tests/setting_up_the_board/test_problem_1_counters.py
```

**1.2 — Can this machine sample?**
Open `tests/setting_up_the_board/problem_2_sampling.py`. Complete
`parts_this_machine_can_finish`. Use the reported counting, sampling and native-execution
capabilities to identify which parts can be run. The test checks cases with and without
sampling.

```bash
python3 -m pytest tests/setting_up_the_board/test_problem_2_sampling.py
```

## Where to go next

[Appendix H](#appendix-h) states the requirements this chapter assumes, and `hardware/README.md`
is the same thing as a checklist. The counter-overflow interrupt that sampling needs is the
Sscofpmf extension @riscv-sscofpmf on RISC-V and a standard part of the PMU on ARM; the reference
board's SoC is documented by its vendor @rpi-bcm2712.

[ch02](#reading-a-listing) is next, on either machine. It teaches reading what the compiler
produced, which every chapter after it assumes you can do.
