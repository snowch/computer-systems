# Choosing a machine

Part III of *Systems From Scratch* is measured on real hardware. This directory says what that
hardware has to be able to do, why it is an ARM machine rather than a RISC-V one, and how to
check the thing you bought.

## The short version

A **Raspberry Pi 5** (4 GB or more) **with the active cooler**. A Pi 4 or Pi 400 you already own
works too.

| | |
|---|---|
| SoC | Broadcom BCM2712 |
| Cores | 4 × Arm Cortex-A76 @ 2.4 GHz, out-of-order |
| Cache | 64 kB L1 I and D per core; 512 kB L2 per core; 2 MB shared L3 |
| RAM | 4, 8 or 16 GB LPDDR4X |
| Storage | microSD, or NVMe via the M.2 HAT |
| `perf` | Counts and samples. `armv8_cortex_a76` PMU, events under `/sys/bus/event_source/devices/` |

Those are the vendor's figures @rpi-bcm2712. The book does not repeat them: ch15 measures that
cache hierarchy and compares what it finds against them, which is more useful than either number
alone.

**The cooler matters.** A Pi 5 throttles under sustained load, and a benchmark whose clock changes
part-way through is not slow, it is wrong. ch14 treats throttling as a measurement hazard and
shows how to catch it; a cooler means you meet it deliberately rather than in every single run.

That is a change from an earlier plan, and the reason is worth a section of its own, because it is
the kind of decision a book should show its working for.

## Why not RISC-V, when Parts I and II are RISC-V?

The book's two targets no longer share an instruction set. That looks like an inconsistency, so
here is the evidence that produced it.

Part III needs `perf` to do two different things: **count** events over a run (`perf stat`) and
**sample** where a program is thousands of times a second (`perf record`). Sampling needs the
counters to raise an interrupt when they overflow. On ARM that has been a standard PMU feature
for years. On RISC-V it is the Sscofpmf extension @riscv-sscofpmf, and support is thin.

A 2025 study measured the three RISC-V cores you can actually buy @riscv-pmu-profiling:

| | SiFive U74 | T-Head C910 | SpacemiT X60 |
|---|---|---|---|
| Boards | VisionFive 2, Milk-V Mars, Star64 | Lichee Pi 4A | Banana Pi BPI-F3, Milk-V Jupiter |
| Out-of-order | No | Yes | No |
| Vector extension | **None** | 0.7.1 (draft) | RVV 1.0 |
| **Counter-overflow interrupt** | **No** | Yes | Limited |
| Upstream Linux support | Yes | Partial | **No** |

> "The SiFive U74, despite better upstream Linux integration, lacks both vector extensions and
> overflow interrupt support, severely limiting traditional performance analysis approaches."

Read down that table and no column wins. The U74 counts but cannot sample and has no vectors —
so ch20 and ch21 become unmeasurable. The C910 can sample but needs a vendor kernel and is
out-of-order. The X60 has the vectors and struggles with `cycles` and `instructions` themselves,
exposing non-standard counters such as `u_mode_cycle` instead. Even SiFive's own flagship P550 is
reported not to support `core_clock_cycles`. On top of that, a VisionFive 2 Ubuntu release
regressed `perf` to "not counted" through a firmware change, and the boards are hard to buy.

So staying on RISC-V would have cost **two of Part III's eight chapters**, plus a hardware hunt,
plus tooling that breaks between distro releases. A Raspberry Pi costs none of those things.

**What it costs instead** is instruction-set continuity between Part II and Part III — and only
in the Part III chapters that actually read disassembly: ch16, ch17 and ch21. The other five are
method, and method does not have an architecture. Appendix F is the translation, written for the
reader who learned RISC-V in ch04 and is about to read AArch64 in ch16. A reader who learned RISC-V assembly in Part I
and then reads AArch64 in ch16 is not being failed by the book; they are being shown that the
concepts were never about RISC-V. That is worth more than the tidiness it replaces.

## What the machine has to do

| | Requirement | Why |
|---|---|---|
| **Must** | AArch64 or RV64 running Linux, reachable over SSH | |
| **Must** | `perf stat -e cycles,instructions -- true` returns real counts | Part III is not possible without it |
| **Must** | `perf record` can sample | ch20 is entirely sampling. Counting and sampling are different capabilities |
| **Must** | 4 GB RAM, 4 cores | ch18 measures what cores cost each other |
| **Nice** | NVMe or a fast SSD | Builds and ch12 are much less tedious |
| **Nice** | A SIMD unit the compiler targets — NEON, or RVV 1.0 | ch21 measures vectorisation |
| **Nice** | An in-order core | Not required, and the reference is out-of-order. In-order cores make ch17 and ch18 easier to read |

## If you already own a RISC-V board

Keep it — Parts I and II are RISC-V and it is a perfectly good machine for the rest. For Part III
it will run everything that counts (ch14 through ch19), and the two chapters it cannot do say so
in their own headers: ch20 needs sampling and ch21 needs a vector unit. Your figures will differ
from the committed ones either way, which is expected.

## Finding something else

If Raspberry Pis are hard to get where you are, paste [`find-a-board.txt`](find-a-board.txt) into
an assistant that can search the web, with your country and budget filled in. It states the
requirements above in a form something else can shop against, and carries the RISC-V findings so
a recommendation cannot walk you back into the problem this section describes.

Treat what comes back as a shortlist, not an answer.

## Before you buy — this is your decision

This book does not sell hardware, has not tested most of what it might point you at, and has no
relationship with any vendor. The prompt hands your requirements to a third-party tool whose
answers nobody here checks: availability and prices change, listings go out of stock, and a
language model will sometimes state a machine's `perf` support with far more confidence than its
evidence supports.

So treat whatever comes back as a lead to verify. Check the retailer, the current price and the
return policy yourself before spending anything.

**The purchase is yours and so is the risk.** Nothing here is a warranty that any machine will
work for you, or that it can be returned if it does not. `LICENSE` and `LICENSE-CODE` disclaim
warranties for the prose and the code alike, and that extends to anything on this page.

One practical consequence worth acting on. **The requirement you cannot check before it arrives
is the one that matters most**: whether `perf` reads hardware counters depends on the kernel and
the device tree rather than on the chip alone, so no product listing can honestly promise it. Buy
from somewhere that accepts returns, and run the check below the day it arrives rather than the
week you reach Part III.

## Then verify, because that is the point

```bash
python3 scripts/verify-setup.py
```

On the machine it reads the device tree and `/proc/cpuinfo`, prints what the core says it is, and
tests **counting and sampling separately** — because a machine can do the first without the
second, and because some configurations report a zero rather than an error, and a zero will
happily propagate into a table. The sampling test spins deliberately and counts the samples it
got back: a profiler asked to sample a sleeping process collects nothing and exits successfully,
which is indistinguishable from a board that cannot sample at all.

If that script is happy, the machine works, whatever anyone recommended. If it is not, no amount
of specification says otherwise.

## Which chapters depend on the reference machine

Most do not. Five do, and each says so in its own header:

| Chapter | Assumes | On different hardware |
|---|---|---|
| ch15 — The Memory Hierarchy | A particular cache hierarchy | The numbers change entirely. Measuring your own is the exercise |
| ch17 — The CPU | An out-of-order, 4-wide Cortex-A76 | Width, predictor and event names differ. An in-order core is *easier* to read |
| ch18 — Memory Ordering on Real Hardware | Four cores, and this interconnect | The scaling curve moves, the mechanism does not |
| ch20 — Whole-Machine Profiling | That `perf` can **sample** | Works on any mainline ARM machine. The chapter most RISC-V boards cannot run |
| ch21 — Vectors | A vector unit — NEON here | On a RISC-V board without RVV 1.0 it reverts to reasoning |

## The reference machine, and why no kernel version is pinned

Figures committed in this repository were measured on the machine each result names — every one
stamps the model, the operating system, the kernel, the core and whether `perf` could count and
sample. Your numbers will differ. The book is about ratios, mechanisms and method, and those
transfer.

What that stamp is *not* is a requirement. It would be easy to name an image and a kernel here,
and the temptation is real, because whether counters work is a property of the whole
configuration and not of the board: the Raspberry Pi kernel's 6.12 branch shipped a Pi 5 device
tree with the `arm-pmu` node missing @rpi-pmu-dt-6507, and on those images the hardware was fine
and `perf` saw nothing.

But a pinned version is the wrong lesson as well as a perishable one. It is wrong within a year,
it cannot be re-verified on every release, and it teaches a reader to compare a string instead of
asking the machine — while the failure it is meant to prevent remains perfectly possible on the
version that was correct when it was written. `verify-setup.py` asks the machine. That answer
stays true.
