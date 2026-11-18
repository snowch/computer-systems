---
title: "00 · Prerequisites and Setup"
short_title: "00 · Prerequisites and Setup"
---

(prerequisites-and-setup)=
# 00 · Prerequisites and Setup

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU, whose toolchain `bare` shares |
| **Prerequisites** | You can write a program in another language and use a terminal. |
| **Evidence** | Your setup report and the book’s recorded xv6 boot and C data layouts. |
:::

## The question

How can you tell whether your computer can build and run the book's emulated examples?

Set up the tools, boot xv6, then inspect the output from a program running inside it. A
successful boot checks more than an installation report because it exercises the build and
the emulator together.

(prerequisites-and-setup-example)=
## Install the tools and run xv6

### Three execution targets

- **`bare`** runs a RISC-V program directly in QEMU, without an operating system.
- **`xv6`** runs programs in the xv6 teaching operating system, also in QEMU.
- **`host`** runs programs on a native Linux machine. Use its hardware counters and clock for
  the timing experiments. The book's reference machine is a Raspberry Pi 5.

A *cross compiler* runs on your computer and builds programs for a different processor. Both
emulated targets use the same RISC-V cross compiler and QEMU. For now, install them on your
computer. Set up native timing hardware in [ch01](#setting-up-the-board) before you need it.

```{figure} _figures/prerequisites-and-setup-targets.svg
:alt: The bare and xv6 targets share a RISC-V emulator on the learner's computer. The host target runs on native Linux hardware.
:width: 100%

Use the two emulated targets to inspect behaviour. Use the native Linux target to measure costs.
```

### Install the tools

On Debian or Ubuntu, open a terminal and run:

```bash
sudo apt install git make build-essential python3-venv gcc-riscv64-linux-gnu qemu-system-misc gdb-multiarch
```

On macOS, use Homebrew in a terminal with Apple's command-line tools installed:

```bash
brew tap riscv-software-src/riscv
brew install riscv-tools qemu python
```

The debugger is used in [Appendix B](#appendix-b). User-mode QEMU and an AArch64 cross compiler
are optional here. They let you check the results of Linux programs built for the reference
board's instruction set without using the board.

### Get the source and check the setup

If this is your first checkout, run the following in the directory where you want to keep the
repository:

```bash
git clone --recursive https://github.com/snowch/computer-systems.git
cd computer-systems
```

The recursive clone also fetches xv6 into `xv6/xv6-riscv/`. If you already have a checkout,
keep your edits, open its root directory and run `make submodule` to fetch xv6 if it is missing.

From the repository root, create and activate a Python environment, install dependencies and
check the tools:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 scripts/verify-setup.py
```

Look for the sections labelled **Target `xv6`** and **Target `bare`**. Confirm the report found
the cross compiler, `qemu-system-riscv64` and the xv6 source. A missing-tool entry tells you what
to install or fetch. The separate `host` report describes whether this machine can collect native
measurements. You can continue with the emulated examples when that report says the board is
unavailable. The separate **Portable C examples** line tells you whether your local compiler
can build examples such as `./run firstc`.

### Boot xv6 and run `sysprobe`

Run the command from your checkout. The build stages a copy of upstream xv6 with the book's
patches and programs in `xv6/stage/`, then starts it in QEMU.

```bash
make xv6-qemu
```

At the xv6 `$` prompt, type `ls` and look for `sysprobe`. Type `sysprobe` to print C type sizes,
structure layouts and byte order. To return to your computer's shell, hold Ctrl and press A,
release both, then press X. QEMU handles this key sequence.

To run the probe in a single command from your computer's shell, use:

```bash
./run sysprobe --target xv6
```

Find `world xv6`, the `type` rows and the `layout` rows in the output. Use the recorded tables
below to identify which fields report byte size and which report alignment. The compiler follows
an *alignment* rule when choosing an address for a value. An alignment of a given number of bytes
requires an address that is a multiple of that number.

### Run a worked example or edit a problem

The page shows read-only examples and recorded output. Edit the named file in your checkout.
Run each command in your computer's terminal, from the repository root. `./run --list` lists the
worked examples by target. The script builds and runs a program, then prints the current output.

Use `./run` to experiment. It writes build files in ignored directories. Keep edits in the source
file you chose or in the problem stub under `tests/`. Leave `xv6/xv6-riscv/` and the generated
`xv6/stage/` alone. The benchmark runners in `bench/` serve a separate purpose. They produce or
check the recorded results printed in the book.

### Check that the two targets agree on data layout

If your computer has the optional AArch64 correctness toolchain or is the native reference
architecture, run the following in your computer's terminal:

```bash
python3 -m pytest tests/test_xv6.py::test_both_targets_give_the_same_answers -q
```

The test runs the same probe on both routes and compares the `types`, `layouts`, `offsets` and
`endian` fields. A skip means the run did not check agreement. A failure names the field whose
values differ. This establishes agreement for the types and layouts in the probe.

```{literalinclude} ../sysfs/include/sysfs/probe.h
:language: c
:start-at: /* Byte order, asked of the machine
:end-before: /* Byte offset of a member
```

The excerpt shows how the probe determines byte order by looking at a byte of a multi-byte value.

## What we measured

These tables report a saved xv6 boot and probe run. The **Conditions** below each table identify
its kernel, compiler and emulator. In the boot table, **Harts started** counts RISC-V hardware
threads. **User programs in the image** counts the programs available to the xv6 shell.

```{include} _generated/prerequisites-and-setup-xv6-environment.md
```

Compare the **Bytes** and **Alignment** columns for `int`, `long` and `pointer`. Which two types
use the same number of bytes in this build? The convention is part of the *application binary
interface* (ABI), the rules compiled code follows for layouts and calls. The RISC-V name for the
variant used here is LP64D @riscv-psabi. [ch13](#representing-information) examines the layouts.

```{include} _generated/prerequisites-and-setup-probe-types.md
```

The two structures below contain the same members in a different order. Compare **sizeof**, the
full size in bytes, with **Bytes that hold nothing**. Which member order needs less padding to
meet the alignment rules?

```{include} _generated/prerequisites-and-setup-probe-layouts.md
```

## What this cannot tell you

An emulated run can show what instructions computed and how the kernel behaved. QEMU timings
depend on the executing computer and the emulator's translation. For program costs, use native
Linux hardware and check its timing tools as described in [ch01](#setting-up-the-board).

The book uses user-mode QEMU to check some programs built for AArch64. Passing those checks
confirms the tested outputs. [ch24](#measuring) explains what to measure on the board and what a
native result can support.

## Problems

Each command runs in your computer's terminal from the repository root. The problem assertion
usually fails on the untouched stub. If setup fails, fix the missing tool or build error before
using the assertion to judge your answer.

**0.1 — Which results can you publish as timings?**
Open `tests/prerequisites_and_setup/problem_1_trust.py` and complete
`can_you_publish_this_timing`. Use the result's `target` and `machine` fields to decide whether
the native hardware produced the result. Run the test and read the case name if it fails.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_1_trust.py
```

**0.2 — Predict the padding.**
Open `tests/prerequisites_and_setup/problem_2_abi.py`. Fill in `EXPECTED_SIZE`,
`EXPECTED_ALIGN` and each value in `EXPECTED_OFFSETS` using the type sizes and alignments above.
Run the test after predicting the layout. The output names any size, alignment or offset that
differs from the compiled structure.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_2_abi.py
```

**0.3 — Your first xv6 program.**
Open `tests/prerequisites_and_setup/ch00ping.c` and complete the TODO so `ch00ping 41` prints
`pong 42`. The test stages that file, boots xv6 and runs it for you. The setup check confirms
that the shell can find and run it. The exercise check looks for the expected output.

```bash
python3 -m pytest tests/prerequisites_and_setup/test_problem_3_xv6.py -q
```

## Where to go next

Continue with [ch02](#reading-a-listing) to read a compiler's output. If you have the native
Linux hardware for performance experiments, use [ch01](#setting-up-the-board) to check its
counters first. You can return to the board setup when you reach [Part V](#part5).

For the source of the data-layout rules, see the RISC-V ABI @riscv-psabi. For the kernel that
boots in this chapter, see the upstream xv6 source @xv6-riscv-source.
