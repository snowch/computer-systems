---
title: "Appendix C · The perf Events This Board Has"
short_title: "Appendix C"
---

(appendix-c)=
# Appendix C · The perf Events This Board Has

Use the tables below to see which events the reference board exposes to `perf`. The names
reflect its processor, kernel and firmware. The Cortex-A76 manual @arm-a76-trm defines the
hardware events. The tables are recorded from `bench/results/perfevents-host.json`.

To inspect a comparable native Linux board, use `python3 -m bench.run_perfevents --check` from
your checkout on that machine. It compares the events and counts reported by the new run with
the saved report without writing a result file.

## What this machine has

```{include} ../chapters/_generated/appendix-c-summary.md
```

## Counted, and computed

How many hardware counters this core has decides whether perf counts or estimates. Up to that
many events run at once, each read straight from its own counter — a *count* of something that
happened. Ask for one more and perf has no counter to give it, so it time-shares them: every event
runs for a fraction of the workload and perf scales its reading up to a whole-run estimate. The
number comes back looking the same and is no longer a count. The figure above found where that line
falls by asking the machine — handing perf one more event at a time until one stopped running for
the whole of the workload.

Carry that distinction out of [Part V](#part5). `perf stat -e cycles,instructions` is two counts; `perf stat`
with a dozen events is a dozen estimates; and the `enabled` percentage perf prints beside each is how
it tells you which you are holding. [ch30](#whole-machine-profiling)'s sampling rests on the same
counters and the same limit.

## The hardware events

The events the PMU counts — the raw names the kernel exposes for this core. The Cortex-A76 manual
@arm-a76-trm defines what they mean, and this book redraws none of it.

```{include} ../chapters/_generated/appendix-c-raw.md
```

perf also offers portable names. These are not events of their own but aliases the kernel maps onto
some of the raw events above — and the mapping is the kernel's choice, not a promise, so
`cache-misses` on one machine and `cache-misses` on another need not be counting the same thing. A
portable name is a convenience, not a definition.

```{include} ../chapters/_generated/appendix-c-generic.md
```

## The software events

`perf list sw` gathers a different kind: events the kernel keeps in software, with no PMU involved,
so they are countable on a machine that has no counters at all — page faults, context switches,
migrations, the CPU clock. Mixed in are perf's own *tool* values, which count nothing and are
computed or simply known: how many CPUs there are, how long the run took. The counted-and-computed
line runs straight through this list too.

```{include} ../chapters/_generated/appendix-c-software.md
```
