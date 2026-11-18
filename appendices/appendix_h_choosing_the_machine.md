---
title: "Appendix H · Choosing the Machine"
short_title: "Appendix H"
---

(appendix-h)=
# Appendix H · Choosing the Machine

Use this page to decide whether a native Linux machine can run the experiments in [Part V](#part5).
Check whether its hardware performance counters can count events and sample where they occur.
[ch01](#setting-up-the-board) gives both tests. You can read the figures and work through the
emulated examples without a native timing machine.

The reference results were recorded on a Raspberry Pi 5 with an active cooler. It is one
configuration that passed the book's checks. The kernel, firmware and device tree affect which
counters Linux exposes.

If you are buying a board, check the seller's return policy and warranty. Run the counters and
sampling checks while the return window is open.

| Item | Reference setup | Why it matters |
|---|---|---|
| Board | Raspberry Pi 5 with 4 GB or more | Four Cortex-A76 cores, with a configuration that exposes hardware counters |
| Cooling | Active cooler or a case with a fan | Helps hold a stable clock under sustained load |
| Power | A USB-C power supply rated for the board | The voltage must remain stable under load |
| Storage | A microSD card or SSD | Holds Linux, the checkout and recorded data |
| Network | Ethernet for remote access | Keeps Wi-Fi driver activity out of quiet timing runs |

(why-a-separate-board-and-not-the-laptop-you-are-reading-this-on)=
## Why use a separate board?

A dedicated measurement machine makes it easier to control what else runs during the experiment.
The reference Pi has identical cores. A different machine can have different core types,
shared execution resources, clock settings or scheduler behaviour. Each can change a result
independently of the program you meant to compare.

The supplied timing runners accept a native AArch64 or RISC-V Linux board with a hardware device
tree. You can use the methods on other native machines, such as an x86-64 Linux laptop, by
adapting the commands and choosing appropriate counters. The supplied runners refuse to record
that setup as a book measurement.

(it-is-an-arm-machine-and-everything-before-part-v-is-risc-v)=
## Why the reference board uses AArch64

The emulated kernel uses RISC-V. The reference board uses AArch64 because its counters can
both count and sample, and its vector instructions allow the experiment in [ch31](#vectors).
A published comparison of three RISC-V cores reported the following capabilities
@riscv-pmu-profiling. Check the **Counter-overflow interrupt** and **Vector extension** rows
to see how those particular cores differ.

| Capability | SiFive U74 | T-Head C910 | SpacemiT X60 |
|---|---|---|---|
| Out-of-order execution | No | Yes | No |
| Vector extension | None | 0.7.1 draft | RVV 1.0 |
| Counter-overflow interrupt | No | Yes | Limited |
| Upstream Linux support | Yes | Partial | No |

[Appendix F](#appendix-f) compares AArch64 and RISC-V instruction syntax. For a different
comparison, read the Pi's specified cache sizes below alongside the measurements in
[ch25](#the-memory-hierarchy). A cache size in a specification describes the product. An
increase in measured access time is evidence about the workload and machine used for that run.

% number-ok: SoC specification from @rpi-bcm2712
The BCM2712 specification lists four Cortex-A76 cores, 64 kB each of L1 instruction and data
cache per core, 512 kB of L2 per core and 2 MB of shared L3 @rpi-bcm2712.

## If you already own something else

On the machine you plan to measure, open a terminal at the repository root and run:

```bash
python3 scripts/verify-setup.py
```

In **Target `host`**, check whether both `cycles` and `instructions` can be counted. Then check
whether `perf record` collected samples. [ch01](#setting-up-the-board) shows how to run each step.
If sampling is unavailable, you can still run the supported counting examples and read the
recorded profiling examples. Check the **Assumes** row of each chapter before reproducing a run.

(the-requirement-to-be-suspicious-about)=
## Why the operating system image matters

The kernel learns which devices it can use from the device tree. The Raspberry Pi kernel's
6.12 branch had a regression that omitted the PMU node for the Pi 5 @rpi-pmu-dt-6507. The counters
were present in the chip, but the kernel did not register the `armv8_cortex_a76` driver or expose
them to `perf`. On RISC-V, firmware also has to expose the counters through the SBI PMU
extension @riscv-sbi.

Run the capability checks on the image you plan to use. Compare remembered or listed kernel
versions with the actual availability of event counts and samples. Each reference result
records its kernel and board, so a reader can tell which configuration produced it.

(the-reference-machine-and-why-your-numbers-will-differ)=
## Compare the conditions before comparing numbers

The values in [Part V](#part5) come from specific workloads on the reference board. Read the
**Conditions** under the figure before comparing your results with it. Changing the cache sizes,
compiler, frequency or background work can change the comparison. [ch24](#measuring) explains
how to decide whether an observed change reflects a version of the program or the test setup.

## Which chapters actually depend on the hardware

Five chapters of [Part V](#part5) list particular hardware assumptions in their headers.
Use the table to see which results you can compare on another machine.

| Chapter | What it assumes | What changes on a different machine |
|---|---|---|
| [ch25](#the-memory-hierarchy) | A particular cache hierarchy — levels, sizes, line size, TLB reach | The numbers, entirely. The method is the chapter, and measuring *your own* hierarchy is the exercise |
| [ch27](#the-cpu) | An out-of-order core, and the PMU events it exposes | Width, predictor and event names all differ. On an **in-order** core these experiments get easier to read, not harder |
| [ch28](#memory-ordering-on-real-hardware) | Four cores, and this interconnect's coherence behaviour | A different core count moves the scaling curve without changing the mechanism. Two cores make the chapter thin |
| [ch30](#whole-machine-profiling) | That `perf` can **sample**, not only count | Standard on a mainline ARM kernel. Most affordable RISC-V cores cannot, so this is the chapter a RISC-V reader will find they cannot run |
| [ch31](#vectors) | A vector unit — NEON here | On a RISC-V board without RVV 1.0 it reverts to reasoning about code the compiler emits but the hardware cannot run |

The repository's `hardware/README.md` has a setup checklist and the tool to check hardware.

## The reference machine's own account of itself

The recorded report in [ch01](#setting-up-the-board) lists the reference model, kernel and
capabilities. Compare its **perf stat** and **perf record** rows with the checks on your machine.

## Where to go next

`hardware/README.md` in the repository carries the same requirements as a checklist, plus the
evidence for choosing an ARM board over a RISC-V one: a 2025 study of the three RISC-V cores that
can actually be bought @riscv-pmu-profiling, and the counter-overflow extension a sampling
profiler needs @riscv-sscofpmf. [Appendix C](#appendix-c) is what this board turned out to
expose once it reported.
