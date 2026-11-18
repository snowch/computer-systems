---
title: "Part V · Where the cycles go"
short_title: "Introduction"
---

(part5)=
# Part V · Where the cycles go

:::{note} Part prerequisites and target
:class: chapter-header

| | |
|---|---|
| **Chapters** | [ch24](#measuring)–[ch31](#vectors) |
| **Target** | `host` — Linux on real hardware, natively ([ch01](#setting-up-the-board)) |
| **Assumes** | [Part IV](#part4), and a machine of your own that meets [Appendix H](#appendix-h)'s requirements |
:::

## What this part is for

Measure the cost of mechanisms you traced earlier. The **Answers the cost of** row links to
the relevant chapter. Use the stated workload and recorded conditions to decide which
comparisons apply to your own measurements.

## What it leaves out

The experiments cover one machine and its operating system. *Systems Performance* @gregg-sysperf covers topics such as tracing, storage and network stacks, and observability across
machines.

## Where to start

Check your hardware with [ch01](#setting-up-the-board), then open [ch24](#measuring). Learn to
separate timer overhead, run-to-run variation and the effect of a deliberate change before you
compare durations.

## Which machine, and what it cannot tell you

Timings are recorded on native Linux. For the reference results, the board and compiler are
identified below each figure. The **Assumes** rows state hardware details that matter to
specific chapters. The reference board runs AArch64. You read a second instruction set in five of them.
[Appendix F](#appendix-f) connects those instructions to RISC-V. [Appendix
H](#appendix-h) explains the choice of hardware and which experiments require sampling or
vector instructions.

## Where this leaves you

You can turn a claim about a program’s performance into a test, choose a workload and counter,
and decide what the result supports.
