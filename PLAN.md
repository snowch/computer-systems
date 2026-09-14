# Systems From Scratch — Book Plan

*From bits to cycles, measured on real hardware.*

The outline, the settled decisions, and the conventions. Read this before writing anything; read
**AUTHORING_GUIDE.md** before writing a chapter; read **CLAUDE.md** before letting an assistant
near either.

---

## 1. What this book is

A self-study text on computer systems and performance, written to answer one question at every
layer of the stack:

> **Where do the cycles go, and how would I know?**

The second clause is the book. Plenty of material will tell you that a cache miss is expensive.
Very little of it will show you how to find out, on a machine in front of you, for a program you
did not write — or how to tell when the answer you got is wrong.

### 1.1 Who it is for

One reader, specifically: someone with basic digital design and computer architecture behind
them, twenty-five years in and around IT, fluent in Python and shell, limited C, and no operating
system internals. The destination is a measurement-driven understanding of performance across the
whole stack — representation, machine code, memory hierarchy, the OS layer, microarchitecture,
whole-machine profiling.

Written for that reader, but written as a real book: if it is any good for one person it is good
for the next person with the same gap.

### 1.2 What makes it different

Four things, and each has a mechanism in the repository behind it rather than a promise.

- **Two targets, and an honest split between them.** A teaching kernel for structure, real
  hardware for cost. Neither is asked the other's question, and the repository refuses to record
  an answer from the wrong one ([§5](#5-hardware-and-execution-strategy)).
- **Every number is stamped.** No figure is typed into prose. Each one traces to a JSON file
  recording target, machine, kernel, compiler, flags and a content hash of the code that produced
  it; CI fails when a quoted number's hash stops matching
  ([§6.3](#63-how-numbers-get-into-the-book)).
- **Every problem is checked by code.** Each chapter's problems are stubs under `tests/chNN/`
  with tests that pass only when solved. There is no answer key, so there is no answer key to be
  wrong.
- **What could not be measured is stated.** The U74 has no vector unit. Some questions cannot be
  asked of QEMU. Every chapter has a mandatory section for what its target and its tooling could
  not show ([§12.1](#121-chapter-template)).

### 1.3 Non-goals

- **Not a RISC-V reference.** The specifications are excellent and free; the book cites them.
- **Not an xv6 commentary.** xv6's authors wrote one. This book uses xv6 as an instrument for
  questions about cost, which is not what that commentary is for, and deliberately does not
  follow its structure ([§10](#10-originality-and-citation-policy)).
- **Not a survey of architectures.** One board, measured properly, beats four described.
- **Not a tuning cookbook.** The subject is how to find out, not a list of tricks.
- **No GPUs, no distributed systems.** Out of scope, and the author has written elsewhere about
  the first.

---

## 2. Relationship to the author's other work

*LLM Serving from Scratch* (snowch/llm-serving-from-scratch) is the closest sibling and the source
of this repository's publishing mechanics: MyST, the stamped-result discipline, the split licence,
the CI shape. Nothing of its content is reused, and it sits one layer up — it measures a serving
system; this book measures the machine underneath one.

The two are complementary reading for a reader who wants the whole column, and each stands alone.

---

## 3. The pedagogical spine

### 3.1 The one question

Every chapter is an instance of *where do the cycles go, and how would I know?* In Parts I and II
the second clause dominates: you cannot ask where the time went until you know what the machine
is doing at all. In Part III the first clause takes over and the second becomes a matter of
technique — which counter, which experiment, which control.

### 3.2 The two targets

The `xv6`/`host` split ([§5](#5-hardware-and-execution-strategy)) is not an implementation
detail, it is the spine. Parts I and II build a complete and *exact* model of what a program does,
on a machine where everything is inspectable and nothing about time is real. Part III takes that
model to hardware and asks what each part of it costs. [ch13](#ch13) is the hinge: the same
program, watched in a debugger and then profiled on the board, with the gap between the two made
explicit.

### 3.3 One book, not two: the pairing

The two targets do not share an instruction set, and the book does not treat that as a seam to be
apologised for. It is the thesis applied to the book's own construction: *use the tool that can
answer your question, and know what each tool cannot tell you.* A RISC-V teaching kernel is the
best available instrument for structure; an ARM machine is the best available instrument for cost.
Picking one instrument for both would mean lying about one of them.

What stops that becoming two tutorials bolted together is a structural device: **Part III is not a
second book, it is Part II's chapters asked again as questions about time.** Each Part III chapter
names the earlier chapter whose cost it measures, in the `answers` field of `bench/outline.py`,
which renders as an **Answers the cost of** row in its header and is checked by
`tests/test_book.py`.

| Part III chapter | Costs what was explained in |
|---|---|
| ch15 The Memory Hierarchy | ch02 (layout and alignment), ch07 (address translation) |
| ch16 Optimising Code | ch04 (what the compiler emitted) |
| ch17 The CPU | ch04 (the instructions), now priced |
| ch18 Memory Ordering on Real Hardware | ch10 (locks, fences, RVWMO) |
| ch19 The OS Layer's Cost | ch06 (traps), ch08 (faults), ch11 (switches) |

Three Part III chapters are deliberately unpaired and the test knows it: ch14 teaches measurement
itself, ch20 is about the whole machine rather than one mechanism, and ch21 concerns hardware Part
II never described. Anything else unpaired is an oversight.

The reader therefore arrives at each Part III chapter already understanding the mechanism and
needing only the price — and the crossing itself is rehearsed once, deliberately, in
[ch13](#ch13).

### 3.4 Measurement as a skill, not a step

A running thread, deliberately spread out rather than confined to [ch14](#ch14): every chapter
that produces a number also says how it could be wrong. Variance, warm-up, the observer effect,
measurement bias @mytkowicz2009wrong, the difference between a correct result and a fast one. By
[ch20](#ch20) the reader should be more suspicious of a benchmark than of a bug report.

---

## 4. Outline

Twenty-two chapters in three parts, plus six appendices. The machine-readable version — number,
slug, title, part, target, checkpoint tag — is `bench/outline.py`, and `tests/test_book.py`
asserts that it, `myst.yml` and the files on disk agree, and that every chapter here declares in
its own header the target it is given below.

Each entry states the **target**, the **objectives**, the **code** the chapter leaves behind, and
the **measurements** it must produce before it can lose its `[DRAFT]` marker.

### Part I — Foundations

Target `xv6` unless stated. The goal of Part I is an exact model of what a program is and what
happens to it, with no hand-waving and no appeals to "roughly".

#### ch00 · Prerequisites and Setup — target `both`

- **Objectives.** Have both targets working; understand why there are two; know that a number's
  provenance is part of the number.
- **Code.** `scripts/verify-setup.py`; `sysfs/include/sysfs/probe.h` and its two front ends;
  `bench/stamp.py`, `bench/measure.py`, `bench/xv6.py`; the staging mechanism for xv6.
- **Measurements.** `setup-xv6` (kernel, emulator, harts, image contents, the C data model as
  reported from inside xv6); `setup-host` (board, image, kernel, whatever the running kernel says
  identifies the core, and whether `perf` can count *and* sample).
- **Listings.** `shapes-riscv64` and `shapes-aarch64` — one small function compiled for both
  architectures, so the instruction-set difference is shown rather than asserted.
- **Problems.** Decide which stamped results may be published; predict a struct's layout before
  compiling it; write a first xv6 user program end to end.

#### ch01 · What a Computer Does With a Program — target `both`

- **Objectives.** One program, followed from source text to result: preprocess, compile, assemble,
  link, load, execute, exit. Which stages are compile-time and which cost anything at run time.
  First encounter with the same program behaving identically and costing differently on the two
  targets.
- **Code.** `sysfs/tools/stages.sh` (or equivalent) that stops the toolchain after each stage and
  keeps the intermediate; a small program used for the rest of Part I.
- **Measurements.** Object sizes and section sizes at each stage (`xv6`); instruction counts for
  the same program under `perf stat` (`host`, pending the board).
- **Problems.** Given intermediates, say which stage produced which. Predict what changes in the
  binary when one source line changes.

#### ch02 · Representing Information — target `xv6`

- **Objectives.** Integers and two's complement as a *representation choice* with consequences;
  bit manipulation; alignment; endianness; where undefined behaviour and overflow actually bite.
  Floating point is introduced on `host` only, because xv6 does not save floating-point registers
  across a context switch — and the chapter explains why that is a reasonable thing for a
  teaching kernel to decide.
- **Code.** `sysfs/lib/bits.c` — the bit operations later chapters reuse, each with a test.
- **Measurements.** Type sizes, alignments and struct layouts across both targets (`xv6`);
  signed-overflow and shift behaviour as the compiler actually emits it.
- **Problems.** Implement a small set of bit operations against a property test; predict the
  layout of several structs; find the input that makes a plausible-looking arithmetic function
  wrong.

#### ch03 · C for People Who Will Read a Kernel — target `xv6`

- **Objectives.** The subset of C that is really about addresses: pointers, casts, arrays versus
  pointers, structs, function pointers, `volatile`, `static`, storage duration. Enough to read
  kernel source without flinching, and no more.
- **Code.** Small, complete programs, each demonstrating one mechanism; a deliberately broken one
  per section for the problems.
- **Measurements.** What the compiler emits for each construct — the disassembly is the evidence,
  and `xv6` is a perfectly good place to read it.
- **Problems.** Read a disassembly and say which C produced it; fix a program that is wrong
  because of a misunderstanding about storage; implement a callback table.

#### ch04 · Machine-Level Code on RISC-V — target `xv6`

- **Objectives.** Registers and their ABI roles; the calling convention; stack frames; how control
  flow compiles; reading `objdump` output and stepping real code in gdb against xv6 binaries.
- **Code.** `sysfs/tools/framewalk.c` — walk a stack from a known frame pointer.
- **Measurements.** Instruction mix and frame sizes for a set of small functions at `-O0` and
  `-O2` (`xv6` — static facts about emitted code, not timings).
- **Problems.** Reconstruct a function's C from its disassembly; predict the frame layout; find
  the register the compiler chose not to save and say why it was allowed to.

#### ch05 · Linking and Loading — target `xv6`

- **Objectives.** ELF: sections, segments, symbols, relocations; what a linker script decides;
  how xv6's `exec` turns a file into an address space.
- **Code.** `sysfs/tools/elfdump.c` — a small ELF reader, written rather than described.
- **Measurements.** Section and segment tables for xv6's own binaries; what `exec` maps, and
  where.
- **Problems.** Implement the parts of `elfdump` that are stubbed; predict which symbols a link
  will resolve; explain a link failure from the error alone.

### Part II — The operating system layer

Target `xv6` throughout, with instrumentation added as patches under `xv6/patches/`. Part II's
goal is that no operating system service remains a black box.

#### ch06 · Traps and System Calls — target `xv6`

- **Objectives.** What hardware does on a trap; what `trampoline.S` and `usertrap` do; the full
  path of one system call; the *cost model* — what work a trap represents even though we cannot
  time it here.
- **Code.** `xv6/patches/06-*` — a syscall counter and a trace facility.
- **Measurements.** Instructions executed on the trap path, counted by instrumentation rather
  than timed; the register and CSR state saved and restored.
- **Problems.** Add a system call end to end; make the tracer report an argument; predict which
  registers must be saved and check against the code.

#### ch07 · Virtual Memory — target `xv6`

- **Objectives.** Sv39; the three-level walk; the kernel address space; `walk`, `kalloc`,
  `mappages`; how a process address space is built and torn down.
- **Code.** `xv6/patches/07-*` — a page-table dumper; `sysfs/tools/sv39.c` — decode a virtual
  address by hand.
- **Measurements.** Page-table shape for a running process: levels, entries, physical pages
  consumed per mapping.
- **Problems.** Decode addresses by hand and check against the dumper; implement the walk; find
  the mapping that explains a fault.

#### ch08 · Page Faults as a Feature — target `xv6`

- **Objectives.** A fault as a mechanism rather than an error: lazy allocation, copy-on-write,
  demand paging. What each buys and what it costs in bookkeeping.
- **Code.** `xv6/patches/08-*` — lazy allocation and COW, with reference counting.
- **Measurements.** Fault counts and pages allocated, with and without each feature, for the same
  workload.
- **Problems.** Implement COW fork against the supplied tests; find the reference-counting bug the
  tests are designed to catch.

#### ch09 · Interrupts and Drivers — target `xv6`

- **Objectives.** UART, PLIC, the timer; interrupt versus trap; top and bottom halves; why a
  driver splits its work in two.
- **Code.** `xv6/patches/09-*` — interrupt counters per source.
- **Measurements.** Interrupt counts by source over a defined workload; buffer occupancy under
  load.
- **Problems.** Add a device driver for a simple virtual device; make the console lose characters
  and explain why it did.

#### ch10 · Locks and Memory Ordering — target `xv6`

- **Objectives.** What a race actually is at the instruction level; spinlocks on `amoswap`;
  fences and what they order; sleep locks; lock ordering and deadlock.
- **Code.** `xv6/patches/10-*` — lock contention counters.
- **Measurements.** Acquisition counts and contention counts per lock; the interleavings that
  break an unlocked counter (deterministic under QEMU, which is the one thing emulation makes
  *easier*).
- **Problems.** Write a correct lock; break a program by removing a fence and explain the result;
  find the lock-order inversion the tests provoke.

#### ch11 · Scheduling and Context Switches — target `xv6`

- **Objectives.** What `swtch` saves and what it does not; the scheduler thread; sleep and wakeup;
  what it means for a thread to "run".
- **Code.** `xv6/patches/11-*` — switch counters and per-process accounting.
- **Measurements.** Context switches per workload; bytes saved per switch; the exact register set.
- **Problems.** Implement a different scheduling policy and show it changes the counts; explain a
  lost wakeup.

#### ch12 · The File System — target `xv6`

- **Objectives.** The seven layers from disk blocks to the file descriptor; the write-ahead log;
  what has to be true on disk for a crash mid-write to be survivable; one `write` traced all the
  way down.
- **Code.** `xv6/patches/12-*` — block-I/O tracing.
- **Measurements.** Block reads and writes for a traced operation; log transactions per
  operation; the amplification factor between a one-byte write and the disk traffic it causes.
- **Problems.** Trace a `write` and account for every block; implement a file-system operation;
  find the state a crash at a specific point would leave behind.

#### ch13 · The Same Program on Both Targets — target `both`

The hinge of the book.

- **Objectives.** Take one program understood completely from Parts I and II, watch it in gdb under
  xv6, then profile it on the reference machine. Confront the fact that the complete structural
  understanding predicts almost nothing about the cost — and work out which parts of the model do
  carry over.
- **The confound, which is the lesson.** Three things differ between the two runs at once:
  emulation versus hardware, one kernel versus another, and one instruction set versus another.
  The chapter must name all three and then *separate* them, because attributing a difference to
  the wrong cause is the most common way to be confidently wrong about performance. This is where
  the reader learns the move the rest of Part III depends on, and it is a better exercise than the
  single-variable version would have been.
- **Code.** The bridge program, built for both targets from one source.
- **Measurements.** Identical structural facts from both targets; the first side-by-side timing
  from the board, against QEMU's meaningless equivalent, shown deliberately.
- **Problems.** Predict, from the Part II model alone, which of several variants will be fastest;
  then measure. The point is the size of the error.

### Part III — Where the cycles go

Target `host` throughout: the reference machine, natively. Every figure in this part is measured
on the board and stamped; nothing here may come from an emulator.

#### ch14 · Measuring — target `host`

- **Objectives.** Clocks and what they cost to read; `perf stat`; cycle counters; repetition,
  variance and what statistic to report; warm-up; the observer effect; measurement bias
  @mytkowicz2009wrong; **thermal throttling**, which the reference machine does under sustained
  load and which silently changes the clock a benchmark is measuring against. How to be wrong
  about a benchmark.
- **Code.** `sysfs/lib/timing.c` and its header — the book's clock. **Joins
  `bench.stamp.CORE_SOURCES` in this chapter**, which invalidates every prior `host` result by
  design; it happens once, here.
- **Measurements.** Clock resolution and read cost; the distribution of a fixed workload over many
  repetitions; the same benchmark made to give three different answers by changing something that
  should not matter; a run long enough to throttle, with the clock recorded alongside the result
  so the reader can see the floor move.
- **Problems.** Build a timing harness against a specification; find the bias in a supplied
  benchmark; make a wrong benchmark right.

#### ch15 · The Memory Hierarchy — target `host`

- **Objectives.** Measure the cache hierarchy rather than look it up: sizes, line size, latency at
  each level, TLB reach. Locality and the miss-rate model.
- **Code.** `sysfs/bench/pointer_chase.c`, `sysfs/bench/stride.c`.
- **Measurements.** Latency versus working-set size; latency versus stride; measured cache and
  line sizes compared with the vendor's figures @rpi-bcm2712; TLB reach.
- **Problems.** Derive the cache parameters from a supplied dataset; predict the miss rate of a
  loop and then measure it.

#### ch16 · Optimising Code — target `host`

- **Objectives.** What the compiler does and does not do; reading optimised output; loop
  transformations; when a source change is real and when it is noise.
- **Code.** `sysfs/bench/loops.c` — the transformation set, each variant a separate function.
- **Measurements.** Each transformation's effect at `-O0`, `-O2` and `-O3`, with the disassembly
  that explains it; at least one case where the optimisation does nothing because the compiler had
  already done it.
- **Problems.** Predict which variants the compiler equalises; make one faster without changing
  what it computes; explain a transformation that made things worse.

#### ch17 · The CPU — target `host`

- **Objectives.** The out-of-order pipeline; branch prediction; instruction-level parallelism;
  reading the A76's PMU events and knowing which are derived rather than measured.
- **Note.** An in-order core would make this chapter easier to read, and the book does not have
  one: the in-order RISC-V option could not sample (§5). The consolation is that every machine a
  reader is likely to optimise is out-of-order, so attributing cycles on a core that reorders them
  is the skill that transfers. The header says so; ch00 says so at more length.
- **Code.** `sysfs/bench/branches.c`, `sysfs/bench/ilp.c`.
- **Measurements.** Misprediction rate versus branch predictability; IPC versus dependency chain
  length; the cost of a mispredict, derived and stated as derived.
- **Problems.** Construct a workload with a target misprediction rate; explain an IPC that is
  lower than the dependency chain predicts.

#### ch18 · Memory Ordering on Real Hardware — target `host`

- **Objectives.** What four cores cost each other: false sharing, cache-line ping-pong, the price
  of atomics and fences — and **a second memory model**, seen next to the first.
- **Why this is not simply "ch10 with numbers".** [ch10](#ch10) teaches RISC-V: `amoswap`, `fence`,
  and RVWMO. This chapter is ARM: load-exclusive/store-exclusive or LSE atomics, `dmb` and its
  domains, and a differently specified model. That is a feature. A reader shown only one weak
  memory model will conclude that model *is* memory ordering; shown two, they learn that "weak
  memory model" is a family, that a fence is an architecture-specific spelling of an
  architecture-independent need, and that the mechanism underneath — store buffers, coherence,
  visible reordering — is what actually transfers. The chapter's job is to make the correspondence
  explicit, not to pretend there is none.
- **Code.** `sysfs/bench/sharing.c`, `sysfs/bench/atomics.c`.
- **Measurements.** Throughput versus sharing distance; atomic operation cost, contended and
  uncontended; fence cost; scaling across one to four cores.
- **Problems.** Find and fix the false sharing in a supplied structure; predict the scaling curve
  before measuring it.

#### ch19 · The OS Layer's Cost on Real Hardware — target `host`

- **Objectives.** What Linux charges for the services xv6 demonstrated: system call, page fault,
  context switch, `mmap`. Compared explicitly against the structural model from Part II.
- **Code.** `sysfs/bench/syscall.c`, `sysfs/bench/fault.c`, `sysfs/bench/switch.c`.
- **Measurements.** Cost of each, with the cheapest available baseline alongside; the cost of a
  minor fault versus a major one; `vDSO` versus a real trap.
- **Problems.** Measure a syscall's cost correctly, avoiding the three traps the chapter has
  already sprung; explain the difference between two measurements of the same call.

#### ch20 · Whole-Machine Profiling — target `host`

- **Objectives.** `perf record`, call graphs, flame graphs; sampling and its biases; the USE
  method; off-CPU time; a method for finding a bottleneck in something you did not write.
- **Code.** `sysfs/tools/profile.sh`; a deliberately misbehaving program to diagnose.
- **Measurements.** Profiles of the supplied program before and after; a sampling artefact shown
  deliberately.
- **Problems.** Find the bottleneck in an unfamiliar program; produce a profile that is wrong, and
  say why.
- **Note.** This chapter is the reason Part III is measured on ARM. It needs `perf record`, and
  sampling needs counter-overflow interrupts, which no affordable in-order RISC-V core provides
  ([§5](#5-hardware-and-execution-strategy)). It is fully measurable on the reference machine, and
  its header warns the RISC-V reader that this is the one chapter they cannot run.

#### ch21 · Vectors — target `host`

- **Objectives.** What vectorisation is and what it buys; when the compiler will do it unasked and
  when it will not; reading vectorised output; the bound a vector unit is actually subject to.
- **Code.** `sysfs/bench/vectorisable.c` — loops that do and do not auto-vectorise, each a
  separate function.
- **Measurements.** Speedup per loop with and without vectorisation; the emitted code that
  explains each; at least one loop the compiler refuses and why; measured against the arithmetic
  bound rather than celebrated on its own.
- **Problems.** Predict which loops the vectoriser can handle and confirm from the emitted code;
  make one it refuses acceptable to it; compute the bound and explain the gap.
- **Note.** This chapter was unmeasurable under the original RISC-V plan — the reference core had
  no vector unit — and became measurable when Part III moved to AArch64 (NEON). A reader on a
  RISC-V board without RVV 1.0 is back in the original situation, and the header says so.

### Appendices

- **A · RISC-V Registers and CSRs** — register roles, the CSRs the book touches, cited to
  @riscv-isa-unprivileged and @riscv-isa-privileged. Redrawn, never reproduced.
- **B · gdb for Kernels and RISC-V** — attaching to QEMU, the xv6 workflow, watchpoints on
  physical memory, what to do when the stack is nonsense.
- **C · The perf Events This Board Has** — generated from the board rather than written: which
  events exist, which are hardware, which are derived. Cannot be completed until the board runs it.
- **D · An xv6 File Map** — what lives where, and which chapter reads it.
- **E · Glossary** — terms with the chapter that defines them.
- **F · AArch64 for RISC-V Readers** — a translation, not a reference. Registers and calling
  convention, the load/store and branch forms, atomics and fences, beside their RISC-V
  equivalents from Part I. Written for someone who has read ch04 and is about to read ch16, and
  deliberately organised as "you know X; here it is again" rather than as an ISA summary.

---

## 5. Hardware and execution strategy

The hardest practical constraint in the book and the one most likely to sink it. Two targets, and
the discipline is that neither is ever asked the other's question.

| Target | What it is | What it answers | What it must never be asked |
|---|---|---|---|
| **`xv6`** | xv6-riscv under `qemu-system-riscv64`, on any machine | Structure and semantics: instruction sequences, system calls, page tables, scheduling, on-disk state | Anything about time. QEMU has no cache, no branch predictor, no store buffer, no pipeline, no memory latency |
| **`host`** | Linux on real hardware with `perf` that can count **and sample**, native, over SSH. Reference machine: a Raspberry Pi 5 | Everything about cost: cycles, misses, mispredictions, syscall and fault costs, scaling across cores | Anything requiring a kernel you can stop mid-trap and modify freely |

**Rules that follow:**

- Every chapter declares its target in its header, and `tests/test_book.py` checks the declaration
  against `bench/outline.py`.
- Every example, figure and exercise states which target it ran on.
- `make bench-board` refuses to run anywhere but the machine itself. `bench.stamp.provenance_problems`
  rejects a `host` result not measured natively on board hardware, and rejects any `xv6` result
  whose summary contains a duration.
- **CI is an x86-64 runner and measures nothing.** It boots xv6 under QEMU for every `xv6`
  example, and cross-compiles every `host` example for AArch64 and runs it under user-mode QEMU
  for *correctness*. Timing tests are marked `board` and skip themselves everywhere else.
- No chapter above `xv6` is a prerequisite for a later `xv6` chapter, so a reader without the
  board can complete Parts I and II in full — fourteen chapters — and set the board up before
  [ch13](#ch13).

**Why the targets do not share an instruction set.** Part III needs `perf` to count *and* to
sample. Sampling requires counter-overflow interrupts — standard on ARM PMUs, and on RISC-V the
Sscofpmf extension @riscv-sscofpmf, whose support is thin. A 2025 study of the three RISC-V cores
that are actually purchasable @riscv-pmu-profiling found none that wins: the SiFive U74 counts but
cannot sample and has no vector unit; the T-Head C910 samples but needs a vendor kernel; the
SpacemiT X60 has RVV 1.0 and struggles with `cycles` and `instructions` themselves. Staying on
RISC-V would have made **two of Part III's eight chapters unmeasurable** (ch20 needs sampling, ch21
needs vectors), on hardware that is hard to buy, with a toolchain that has regressed between distro
releases.

The cost is instruction-set continuity, and it falls on the three chapters that read disassembly —
ch16, ch17, ch21. The other five are method, and method has no architecture. A reader meeting
AArch64 in ch16 after learning RISC-V in ch04 is being shown that the concepts were never about
RISC-V, which is worth more than the tidiness it replaces. `hardware/README.md` carries the
evidence; ch00 makes the argument to the reader.

**Why a capability, not a part number.** The book originally named one board. Its retailer listing
went out of stock while ch00 was being written, and the named variant proved hard to buy in the UK
at all. A book outlives a product listing, so `hardware/README.md` states what the machine must
*do* and `hardware/find-a-board.txt` is a prompt the reader hands to an assistant that knows
today's stock. Nothing rests on that recommendation being right: `scripts/verify-setup.py`
interrogates the machine that actually arrived, and `perf` either reads hardware counters or it
does not.

**What the requirement insists on.** Counting **and** sampling — the one thing with no workaround,
and two capabilities rather than one, since a machine can have the first without the second. Four
cores, for ch18. Everything else is preference, including in-order execution: it makes
microarchitecture legible, the reference machine does not have it, and ch17 says so and is more
transferable for it, because every machine a reader wants to optimise is out-of-order.

**What follows from readers having different machines.** Absolute numbers are reader-specific, so
the prose argues in ratios, mechanisms and method, and every figure stamps the machine that
produced it. Committed figures come from the reference machine; ch15 in particular becomes
"measure *your* cache hierarchy" rather than a table to memorise, which suits the book's question
better anyway.

**Five chapters depend on the reference core, and must say so.** The dependency is recorded in
`bench/outline.py` as a chapter's `assumes` field, which `scripts/new-chapter.py` renders as an
**Assumes** row in the chapter header, and which `tests/test_book.py` requires to appear both
there and in ch00's list. A reader opens one chapter, not the book, so the warning has to be
where they land — and recording it as data rather than prose is what stops it being dropped when
the chapter is finally drafted.

| Chapter | Assumes | Effect elsewhere |
|---|---|---|
| ch15 | A particular cache hierarchy | Numbers change entirely; the method is the chapter |
| ch17 | An out-of-order, 4-wide core and its PMU events | Width, predictor and event names differ; an in-order core is *easier* to read |
| ch18 | Four cores and this interconnect's coherence | Scaling curve moves; mechanism does not |
| ch20 | That `perf` can **sample**, not only count | Standard on mainline ARM; the chapter a RISC-V reader cannot run |
| ch21 | A vector unit (NEON) | On a RISC-V board without RVV 1.0 it reverts to reasoning |

No other chapter may acquire a hardware dependency silently: if it needs one, it gets an
`assumes` entry, and the tests then insist the reader is told.

---

## 6. Companion code

### 6.1 Layout

The code lives in the **same repository** as the book, so a chapter and its code cannot drift.

```
computer-systems/
├── sysfs/                  # the companion C library and tools, built up across the book
│   ├── include/sysfs/      # headers, shared between the two targets
│   ├── lib/                # shapes.c (the functions ch04 reads), bits.c (ch02), timing.c (ch14)
│   ├── tools/              # elfdump, framewalk, sysprobe, profile.sh
│   └── bench/              # the host-target microbenchmarks (Part III)
├── bench/                  # the book's Python tooling
│   ├── outline.py          # the book's shape, machine-readable
│   ├── stamp.py            # what a result must carry, and where it may come from
│   ├── measure.py          # building and running C; repetition and statistics
│   ├── disasm.py           # objdump output as a stamped artefact
│   ├── xv6.py              # staging, building and driving the teaching kernel
│   ├── figures.py          # every table, listing and diagram, declared once
│   ├── tables.py           # results to markdown
│   ├── diagrams.py         # figures, drawn by code, as deterministic SVG
│   ├── run_*.py            # the runners that produce results
│   └── results/*.json      # committed, stamped
├── xv6/
│   ├── xv6-riscv/          # submodule: upstream, never modified
│   ├── apps/               # the book's xv6 user programs
│   ├── patches/            # the book's kernel instrumentation, as diffs
│   └── stage/              # generated, not in git
├── tests/                  # the book's own tests, plus tests/chNN/ — the reader's problems
├── chapters/               # ch00.md … ch21.md, plus _generated/ and _figures/
├── appendices/
└── scripts/                # verify-setup, render-figures, verify-numbers, build-pdf, ci-check
```

`sysfs/` is named for the book, and collides with the name of Linux's `/sys` filesystem. That is
unfortunate and deliberate: the alternative names were worse, the directory is only ever referred
to as a path, and the book says so here so that nobody spends ten minutes confused.

### 6.2 Per-chapter checkpoints

Readers must be able to start anywhere. Two mechanisms, both in **CHECKPOINTS.md**: a git tag per
chapter that changes the code, and a table mapping chapter to tag to the state of the companion
code at that point.

Chapter text quotes code from the working tree with MyST's `{literalinclude}`, anchored on
`:start-at:` / `:end-before:` **text**, never line numbers, which rot on the first edit above
them. `tests/test_book.py` fails a chapter that uses `:lines:`. Code is never pasted into prose:
copy-pasted code goes stale within two chapters.

**Machine code is the one thing that cannot be quoted from the tree**, because it does not exist
there until a compiler has run. Chapters 4, 16 and 17 need it anyway, so `bench/disasm.py`
compiles a named function to an object file, disassembles it with the matching `objdump`, and
writes the output as a stamped result — see §6.3.

### 6.3 How numbers get into the book

1. A runner under `bench/run_*.py` produces a result and writes it to `bench/results/<name>.json`
   via `bench.stamp.write_result`, which stamps target, machine, kernel, toolchain, flags, and a
   content hash over `CORE_SOURCES` plus the runner's own sources.
2. Each figure is declared once in `bench/figures.py` and rendered to `chapters/_generated/*.md`
   (tables and listings) or `chapters/_figures/*.svg` (diagrams) by `scripts/render-figures.py`.
   Chapters pull them in with `{include}` and `{figure}`.
3. Three CI guards: `scripts/verify-numbers.py` (every cited result exists, carries its stamps,
   matches the code checked in, and was produced somewhere it was allowed to be produced),
   `scripts/render-figures.py --check` (every committed fragment still matches the results), and
   `python3 -m bench.run_disasm --check` (every listing is still what this compiler emits).

**Listings are a second kind of result.** A result declares a `kind`: almost all are
`measurement`, and disassembly is a `listing`. The two need opposite provenance rules, which is
why the distinction exists rather than being a naming convention:

| | `measurement` | `listing` |
|---|---|---|
| Depends on | the machine it ran on | the compiler that produced it |
| A `host` one requires | the reference machine, natively | nothing — any machine with the cross compiler |
| May contain a duration | yes, on `host` | **never**, on either target |
| CI can regenerate it | no | **yes, and does, on every push** |

The last row is the payoff and the third row is its price. Exempting listings from the board rule
would otherwise be a one-word way round the check the whole scheme rests on, so
`bench.stamp.provenance_problems` holds a listing to its own shape: no timing keys anywhere in it,
`measured_under: compilation`, and a summary containing nothing but listings.

**Chapters contain no executable cells.** Rendering figures by executing code during the book
build makes every deploy depend on a toolchain, and here it would make the deploy depend on a
RISC-V toolchain and QEMU, which is absurd for publishing a web page. Pre-rendering keeps the
build pure markdown and lets CI *diff* the regenerated output — a stronger staleness guarantee
than execution provides.

**Pending figures.** Part III is measured on hardware CI does not have. A figure whose measurement
has not been taken is declared `pending=` and renders as a warning naming the command that would
produce it. It contains no numbers at all — not even placeholder ones — so a draft can never be
mistaken for a measurement; and `verify-numbers.py` fails if a pending figure's result file
exists, so a measurement that has landed cannot be left marked missing.

**No number is ever typed into prose.** `verify-numbers.py` scans chapter text for figures
carrying a cost unit and fails the build. A cited specification is allowed, marked with a
`% number-ok: <citation>` comment on the line before so the reason is visible in review.

### 6.4 Correctness testing

- Every `xv6` example is exercised by booting the kernel under QEMU in CI.
- Every `host` example is cross-compiled for the reference architecture and run under user-mode
  QEMU in CI. Correctness only — and the flags differ from the board's (`-static`), which the
  chapter says wherever it matters.
- Every disassembly listing the book prints is re-captured in CI and diffed against what is
  committed, so a compiler that changes its mind fails the build rather than a reader's afternoon.
- Timing tests are marked `board` and skip everywhere else.
- The reader's problems are marked `problem` and deselected in CI; the **scaffolding** beside each
  is not, so CI proves every problem is answerable without asserting anyone has answered it.

---

## 7. Toolchain

| Thing | Where it is pinned | Notes |
|---|---|---|
| `mystmd` | `package.json` | The book builder. From npm, pinned; never duplicated in `requirements.txt`. |
| Python deps | `requirements.txt` | One line: PyYAML. The companion code is C; Python drives compilers and stamps JSON. |
| Lint and test | `requirements-dev.txt` | `ruff` pin must match `.pre-commit-config.yaml`. |
| RISC-V toolchain | documented, not pinned | `riscv64-linux-gnu-gcc` or `riscv64-unknown-elf-gcc`; recorded in every result rather than pinned, because the board's compiler is the board's business. |
| QEMU | documented, recorded | Version stamped into every `xv6` result. |
| xv6 | `.gitmodules` | Pinned by submodule commit, and recorded in every `xv6` result. |

---

## 8. Repository layout

See [§6.1](#61-layout). Documents at the root: `PLAN.md` (this), `AUTHORING_GUIDE.md`,
`CHECKPOINTS.md`, `CLAUDE.md`, `ORIGINALITY.md`, `ERRATA.md`, `README.md`, and the split licence
(`LICENSE` for prose, `LICENSE-CODE` for code).

---

## 9. Build and publishing pipeline

**`quality.yml`** — every push and pull request. Installs the RISC-V cross compiler,
`qemu-system-misc` and `qemu-user-static`, then runs `scripts/ci-check.sh`, which is the single
source of truth for what CI does:

- `ruff check` and `ruff format --check` over `bench/`, `scripts/`, `tests/`
- `pytest -m "not problem"` — the book's tests, including booting xv6 and running RV64 binaries
- `scripts/verify-numbers.py` — stamps, hashes, provenance, no typed figures
- `scripts/render-figures.py --check` — every committed fragment and diagram current
- `myst build --strict` — every cross-reference, citation and `literalinclude` anchor resolves
- `scripts/build-pdf.py --html-only` — the PDF renderer sees every page and raises on any node
  type it does not handle
- the themed HTML build, mandatory in CI

It then re-runs the xv6 measurement and fails if the committed result no longer matches a fresh
boot — the guard against a kernel patch that changes the answers without anyone re-rendering.

**`deploy.yml`** — push to `main` and manual dispatch. Builds the site with `BASE_URL` set from
the Pages base path, builds the single-file PDF with Chromium, and publishes with the
retry-and-backoff pattern.

### CI mistakes to avoid

1. **A `workflow_run` trigger naming a workflow that does not exist**, which silently reduces
   deployment to manual dispatch only. Deploy triggers directly on push here.
2. **Lint paths that do not match real directories.** `ci-check.sh` is the single source of truth
   that CI, `pre-commit` and a person all invoke, so drift is impossible.
3. **Unpinned `mystmd`.** `npm install -g mystmd` installs whatever is latest, so a build that
   worked yesterday breaks with no commit.
4. **Cache staleness.** `bench/results/*.json` is in the cache key, so a new measurement
   invalidates anything cached.
5. **A test that reads `_build/`.** A local checkout has one left from earlier work and a CI runner
   never does, so such a test passes locally and fails in CI.
6. **Bare `pytest`.** Use `python3 -m pytest`, so tests run under the interpreter that has the
   dependencies. A standalone pytest has its own environment and cannot import `bench`.
7. **Assuming CI can measure.** It cannot, and it must never be made to look as though it can.

---

## 10. Originality and citation policy

This is a crowded subject and the book must be **entirely original work**. The full rules, which
bind both the author and any assistant, are **CLAUDE.md §5**. In summary:

- No reproduction, close paraphrase, or structural mirroring of any existing book, lecture notes
  or course material — including the well-known ones on exactly these topics. Not their chapter
  structure, section headings, figures, example programs, problem sets, or characteristic
  phrasings. Noticing that a sequence or an example is a known one is a reason to design a
  different one.
- Ideas, facts, algorithms and public specifications are not copyrightable; expression is. Same
  concepts, own structure, own examples, own figures.
- **Source code.** xv6 is MIT: short attributed excerpts are fine and encouraged, and this book's
  changes ship as patches, never as a copied tree. The RISC-V specifications are permissively
  licensed: cite them, redraw what is needed, never reproduce tables wholesale. Linux excerpts are
  GPL: very short, attributed, and prefer describing behaviour to quoting code. Never reproduce
  code from a textbook.
- **Citations.** Every factual claim about hardware behaviour cites either a measurement in
  `bench/results/` or a primary source in `references.bib`. Textbooks appear only in a chapter's
  "Where to go next", never as a source for its content.
- **ORIGINALITY.md** records, per chapter, the works closest to it in subject and one line on how
  this chapter's structure and examples differ. Updated in the same commit as the chapter, and
  `tests/test_book.py` fails a finished chapter that has no entry.

---

## 11. Delivery roadmap

| Milestone | Contents | State |
|---|---|---|
| **M0 — scaffold** | Repository, pipeline, stamping mechanism, xv6 submodule and staging, `verify-setup.py`, ch00 complete, stubs for everything else | **done** |
| **M1 — the board** | `make bench-board` run on the reference machine; `setup-host` committed; Appendix C generated | needs the hardware |
| **M2 — Part I** | ch01–ch05, `sysfs/lib/bits.c`, `elfdump`, `framewalk` | next |
| **M3 — Part II** | ch06–ch12 with kernel patches and per-chapter instrumentation | |
| **M4 — the hinge** | ch13, both targets, first real comparison | needs M1 |
| **M5 — Part III** | ch14–ch21, every figure measured on the board | needs M1 |
| **M6 — v1.0** | Appendices complete, ERRATA reconciled, plagiarism check clean, PDF published | |

Part III cannot start before M1, and nothing in M2 or M3 depends on it. That ordering is the point
of the two-target design: fourteen chapters of real work are available before the hardware is.

---

## 12. Conventions and quality bar

### 12.1 Chapter template

Seven parts, in this order, every time. The repetition is what makes twenty-two chapters read as
one book.

1. **Header block** — target, prerequisites, what it measures and where the result lands.
2. **The question** — one paragraph. What this chapter answers, and why the previous one leaves
   it open.
3. **The material** — the body. Short sections. Code quoted from the working tree.
4. **What we measured** — generated fragments only. No number typed in prose.
5. **What this cannot tell you** — **mandatory**. What the target, the tooling or the hardware
   could not show, and what was done instead. A chapter is not finished while this is missing; it
   is the section that makes the rest believable.
6. **Problems** — each a stub under `tests/chNN/` with a test that passes only when solved.
7. **Where to go next** — primary sources via `@citekey`. Textbooks may appear here and nowhere
   else.

### 12.2 Style

- British English, direct, active voice, short sentences. First-person plural sparingly.
- No marketing tone, no filler, no "in this chapter we will".
- Mathematics only where it predicts something the reader then verifies.
- Every figure must show a mechanism. No decorative diagrams, no screenshots of anyone else's
  work. Figures are SVG drawn by `bench/diagrams.py`, deterministic so staleness can be checked.
- Every number carries its conditions: target, machine, kernel, compiler, flags, date.
- Prefer showing a measurement that surprises the reader over asserting a rule.
- `[DRAFT]` stays in the title until [§12.3](#123-definition-of-done-per-chapter) is met.

### 12.3 Definition of done (per chapter)

- [ ] Problems written **first**, each failing for the right reason, marked `problem`
- [ ] Scaffolding tests beside them, unmarked, proving the problems are answerable
- [ ] Companion code merged, passing `ruff` and building on its declared target in CI
- [ ] Every figure declared in `bench/figures.py` and rendered from a committed result — or
      declared `pending=` with the command that produces it
- [ ] "What this cannot tell you" written
- [ ] `ORIGINALITY.md` entry added in the same commit
- [ ] Cross-references and citations resolve; `./scripts/ci-check.sh` clean
- [ ] Checkpoint tag pushed, `CHECKPOINTS.md` updated
- [ ] `[DRAFT]` removed

### 12.4 Version pinning and staleness

Hardware and compilers move slowly; the tooling around them does not. So: `mystmd` and the Python
tools are pinned exactly, with the date verified in a comment. The RISC-V toolchain and QEMU are
*recorded* rather than pinned — the board's compiler is whatever the board has — which is why
every result stamps the compiler's full version string rather than a paraphrase of it. A
distribution's patch level moves a benchmark by a few per cent, and an unrecorded one makes that
unexplainable a year later.

`CORE_SOURCES` in `bench/stamp.py` should be treated as frozen once chapters cite results.
[ch14](#ch14) adds the timing library to it, once, deliberately, invalidating every earlier
`host` result. Any later change to it means regenerating everything, on the board.

---

## 13. Decisions — settled

Recorded so they are not relitigated.

1. **Two targets, not one.** A single target would mean either no real timings or no inspectable
   kernel. The split is the book's argument.
2. **The targets do not share an instruction set, and Part III is ARM.** Decided on evidence
   ([§5](#5-hardware-and-execution-strategy)): no purchasable RISC-V core both counts and samples,
   which would have cost ch20 and ch21. Instruction-set continuity was worth less than two
   chapters, and only ch04, ch16 and ch17 depend on reading disassembly. Revisit if a RISC-V
   board appears that counts, samples, has RVV 1.0 and upstream Linux support — at which point
   the reference machine can move back and only `hardware/` and five chapter headers change.
3. **xv6 as a submodule plus patches, never a fork.** `ls xv6/patches/` must remain a complete
   answer to what the book changed.
4. **The board is the only place a timing may be measured.** Enforced in code, not in prose.
5. **CI proves correctness, never cost.** Cross-compilation plus user-mode QEMU, marked as such
   everywhere it appears.
6. **No executable cells in chapters.** Pre-rendered fragments, diffed in CI.
7. **Pending figures show nothing rather than something plausible.** A missing measurement
   announces itself; a placeholder does not.
8. **Problems are tests, not an answer key.** Marked `problem`, deselected in CI, with scaffolding
   checked separately.
9. **Figures are hand-built deterministic SVG, not matplotlib.** A plot whose bytes change on a
   library upgrade cannot be checked for staleness, and a check people learn to ignore is worse
   than no check.
10. **British English, and the book's voice is the author's.**
11. **Split licence**: CC-BY-NC-4.0 for prose, Apache-2.0 for code, MIT retained for xv6 and for
    patches against it.

---

## 14. Immediate next steps

1. Run `make bench-board` on the reference machine, commit `bench/results/setup-host.json`, and
   remove the `pending=` marker on `ch00-board` in `bench/figures.py` (M1).
2. Generate Appendix C from the board — the `perf` events it actually has.
3. Write ch01 with the per-chapter prompt, following
   [§12.1](#121-chapter-template) and [§12.3](#123-definition-of-done-per-chapter).
4. As Part I lands, keep `ERRATA.md` honest about anything a later chapter contradicts.
