# Choosing a board

Part III of *Systems From Scratch* is measured on real RISC-V hardware. This directory says
what that hardware has to be able to do, and hands you a prompt for working out what to buy.

## Why the book does not name one board

It used to. The problem is that a book outlives a product listing: while this page was being
written, a linked retailer listing for the reference board went out of stock, and the exact
variant originally specified — a cut-down "Lite" model — turned out to be hard to buy in the UK
at all. A book that hard-codes a SKU is a book with a broken first chapter within a year.

So the requirements below are stated as **capabilities**, which are stable, and the shopping is
delegated to something that knows what today's stock is. What makes that safe rather than
hopeful is that nothing depends on the recommendation being right: `scripts/verify-setup.py`
interrogates the board you actually bought and tells you whether it can do the job.

## What the board has to do

| | Requirement | Why |
|---|---|---|
| **Must** | RV64GC (`rv64imafdc`) application processor running Linux, reachable over SSH | The ISA read in a debugger in Part I is the ISA measured in Part III — no translation in your head |
| **Must** | `perf stat -e cycles,instructions -- true` returns real counts | Part III is not possible without it. **The one requirement with no workaround** |
| **Must** | 4 GB RAM (8 GB preferred), 2 cores (4+ preferred) | ch18 measures what cores cost each other |
| **Prefer** | An in-order core, SiFive U74 family or similar | ch17 and ch18 explain microarchitecture by measuring it, and an in-order core makes the effects legible |
| **Prefer** | In production, still receiving distro images | An abandoned vendor kernel is where `perf` support goes to die |
| **Nice** | M.2 NVMe | Builds and ch12 are much less tedious |
| **Nice** | RVV 1.0 vector support | ch21 currently reasons about vectorisation because the reference hardware has no vector unit |
| **Nice** | 3.3 V UART header | For watching a boot that never reaches the network |

The counter requirement is the one to be suspicious about. On RISC-V the counters are reached
through the firmware's SBI PMU extension rather than directly, so whether `perf` works is a
property of the shipped software image as much as of the silicon — and a datasheet saying the
core has a hardware performance monitor tells you nothing about whether you can read it.

## Finding one

Paste [`find-a-board.txt`](find-a-board.txt) into an LLM that can search the web, filling in
your country and budget. It states the requirements above in a form something else can shop
against, and it asks for a source for the `perf` claim specifically, because that is the claim
most likely to be confidently wrong.

Treat what comes back as a shortlist, not an answer.

## Before you buy — this is your decision

This book does not sell hardware, has not tested most of what it might point you at, and has no
relationship with any vendor. The prompt above hands your requirements to a third-party tool
whose answers nobody here checks: availability and prices change constantly, listings go out of
stock (one did while this page was being written), and a language model will sometimes state a
board's `perf` support with far more confidence than its evidence supports.

So treat whatever comes back as a lead to verify, not a recommendation to act on. Check the
retailer, the current price and the return policy yourself before spending anything.

**The purchase is yours and so is the risk.** Nothing here is a warranty that any board will work
for you, or that it can be returned if it does not. `LICENSE` and `LICENSE-CODE` disclaim
warranties for the prose and the code alike, and that extends to anything on this page.

One practical consequence worth acting on. **The requirement you cannot check before it arrives
is the one that matters most**: whether `perf` reads hardware counters depends on the firmware
and the distro image rather than on the chip alone, so no product listing can honestly promise
it. Buy from somewhere that accepts returns, and run the check below the day the board arrives
rather than the week you reach Part III.

## Then verify, because that is the point

```bash
python3 scripts/verify-setup.py
```

On the board it reads the device tree and `/proc/cpuinfo`, prints the ISA string and the core's
vendor and architecture IDs, and runs the `perf` check — distinguishing "counted" from "counted
something greater than zero", because some configurations report a zero rather than an error and
a zero will happily propagate into a table.

If that script is happy, the board works, whatever anyone recommended. If it is not, no amount
of specification says otherwise.

## The reference machine

The figures committed in this repository were measured on a **StarFive VisionFive 2 Lite**
(JH7110S, 4× SiFive U74) unless a result says otherwise — and every result does say, because
each one stamps the board model, ISA string and core IDs of the machine that produced it.

So your numbers will differ from the committed ones, and that is expected rather than a problem.
The book is about ratios, mechanisms and method, and those transfer.

Four chapters do depend on properties of this core, and each says so in its own header:

| Chapter | Assumes | On a different board |
|---|---|---|
| ch15 — The Memory Hierarchy | A particular cache hierarchy | The numbers change entirely. Measuring your own is the exercise |
| ch17 — The CPU | An in-order pipeline, and this core's PMU events | Experiments still run; out-of-order results are harder to attribute |
| ch18 — Memory Ordering on Real Hardware | Four cores, and this interconnect | The scaling curve moves, the mechanism does not. Two cores make it thin |
| ch21 — Vectors | **No vector unit** | With RVV 1.0 you can measure what the chapter only reasons about |

Worth reading before you buy: a two-core board makes ch18 thin, and a vector-capable one makes
ch21 better than it is for the author.
