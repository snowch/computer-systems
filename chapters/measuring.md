---
title: "Measuring"
short_title: "24 · Measuring"
---

(measuring)=
# 24 · Measuring

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Prerequisites** | [ch23](#the-same-program-on-both-targets) |
| **What it measures** | The instrument, before anything is measured with it: `bench/results/measuring-host.json` |
:::

## The question

How do I get a number I would defend, and how would I know it was wrong?

[ch23](#the-same-program-on-both-targets) established that the structural model does not predict cost, and pointed at a
machine that can answer. This chapter first measures what reading the clock costs, then changes
something about the program that should make no difference, and checks whether the answer moves.

## The material

### The instrument is part of the measurement

Every duration in this book is read through one header, so that "how was this timed" has one
answer rather than one per chapter. It reads the *monotonic* clock — one that only ever goes
forward and is never adjusted to keep wall-clock time honest, so a measurement cannot come out
negative because something corrected the date halfway through:

```{literalinclude} ../sysfs/include/sysfs/timing.h
:language: c
:start-at: uint64_t sysfs_now_ns(void);
:end-before: /* The distribution
```

The second function is the one people skip. Reading a clock takes time, that time is included in
every measurement made with it, and if the thing being measured is of the same order then the
instrument is most of what is being measured.

```{include} _generated/measuring-clock.md
```

The first two numbers there measure different things. What a clock *costs* is how long the read
takes. What it can *resolve* is the smallest change it will ever report — a clock can hand back
nanoseconds and still only ever move in steps of a hundred of them, in which case a measurement of
anything shorter is a coin toss between zero and one step. The third row is what the first
implies: work that costs as much as reading the clock is half instrument.

Problem 24.2 turns this into the arithmetic you actually need: given what the work costs and what
the clock costs, how many repetitions must go inside one timed region before the instrument is
small enough to ignore.

### There is no such thing as the time it took

Run identical work, on an idle machine, two thousand times:

```{include} _generated/measuring-spread.md
```

Read the 90th percentile against the fastest, and then the slowest. Identical work, identical
input, nothing else running — and yet nine runs in ten agree to within a rounding error while the
slowest stands far outside them. Nothing was wrong with any of those measurements; they are all
correct observations of what happened.

So "how long does it take" has no answer, and the question has to change. Report a distribution
instead, which is why `sysfs_summarise` exists and why problem 24.1 asks you to write it.

**Why the minimum is usually the number to look at.** Everything that can happen to a measurement
on a real machine makes it slower: an interrupt arrives, another process is scheduled, a page is
not resident, the clock drifts. Almost nothing makes it faster. So the mean is partly a statement
about the interference and the minimum is the closest available statement about the work.

**And when that reasoning fails.** If you care how long something takes *in service*, the
interference is not noise — it is the thing your users experience, and reporting the minimum is
reporting the one case that never happens to them. Two different questions, two different
statistics, and the mistake is not picking the wrong one but not noticing there was a choice.

### Why the first measurements are slow

The first few measurements are slower, always, for three reasons the chapters either side of this
one take apart: [ch18](#page-faults-as-a-feature)'s pages are not yet faulted in, [ch25](#the-memory-hierarchy)'s caches hold somebody
else's data, and the branch predictor of [ch27](#the-cpu) has never seen this loop.

Discarding them is standard practice and is usually done wrong. Warm-up is a property of
*position*: the first samples are slow because they are first. A slow sample in the middle is
interference, it is not warm-up, and discarding everything before it throws away good
measurements in order to hide a bad one. Problem 24.3 is that distinction, which is why the
definition it asks you to implement has a second clause.

### The variable that should not matter

Here is the experiment every benchmark deserves and few get: vary something that cannot affect the
result, and check that the result does not move.

The same work, the same input, the same binary, three times — differing only in how many bytes of
stack were claimed before the buffer it walks was allocated. Not used. Claimed. Each run lands the
data at a different address, and the runner records that address, so this is a real change to where
everything sits and not padding the compiler quietly folded away.

```{include} _generated/measuring-bias.md
```

The addresses differ; the median does not move by a nanosecond. On this core, where the data sits
does not change what reaching it costs.

On other machines it does move. Mytkowicz and colleagues @mytkowicz2009wrong made the same change —
they varied the size of an environment variable, which moves the stack, exactly as the padding here
does — and found it large enough to manufacture or erase the kind of speedup papers are published
about. Their machine cared. This one, measured the same way, does not, very likely because a core
with this much first-level cache, and this forgiving an attitude to unaligned access, hides what a
2009 one could not.

The null result does not make the experiment less worth running. You cannot tell which machine you
have by reasoning about it — Mytkowicz and colleagues could not, and neither could this chapter
until the board answered. A single configuration, measured carefully, can be confidently wrong, and
no amount of repetition inside it ever finds out. So do not conclude the effect is gone because
this page did not find it. Vary the thing that should not matter, on your own machine, and see
whether your result survives.

### The floor moves

One more source of slow samples, specific to this book's reference machine and to most small ones.

A Raspberry Pi 5 under sustained load gets hot and reduces its clock. Not gradually and not with a
warning: the frequency drops, and every measurement after that point is against a different
machine from the ones before it. A benchmark that runs for a minute can therefore show a
"regression" in its second half that is entirely thermal — and a comparison between two
implementations, run one after the other, can rank them by which went first.

The defence is to record the clock alongside the result, which is why [Appendix H](#appendix-h) insists on the
active cooler and why every `host` result in this book stamps the machine's state as well as its
number. It is also why the results are taken with the board idle and the laptop not driving it
over a link that interrupts it, which is the next section's subject.

### What else the machine is doing

[ch01](#setting-up-the-board) recommends wiring the board rather than using its radio, and gives a mechanism: a
wireless driver takes interrupts and runs deferred work on the cores being measured, which is
[ch19](#interrupts-and-drivers)'s subject arriving where it is least wanted.

So: the same fixed workload, run many times over with the radio off and again with it on — the only
thing changed being a variable that has nothing to do with the code.

```{include} _generated/measuring-interference.md
```

Read the first row before any other. The fastest sample is identical to the nanosecond, radio or
not, because interference can only ever add time: the fastest run is the one it missed. That is the
earlier argument for the minimum, demonstrated rather than asserted — everything the radio does
makes a measurement slower, so the mean carries the interference and the floor carries the work.

Now read the rest of the table. A clean run with the radio on is indistinguishable from one with it
off, so a single measurement cannot tell you which you have: the radio's background work arrives in
bursts, and only a run that catches one is wrecked — its mean dragged well above the floor while
its neighbours look fine. Which run you happened to take decides your answer, and nothing inside
that run tells you which kind you got. It is the warm-up problem inverted: not a slow prefix you
can cut, but slow samples scattered through a run that averages out clean until it does not.

Wiring the board does not make it faster. It makes the number mean something, by removing a source
of slow samples the work has no say in. The radio is one such source; a busy neighbour, a background
build, a cron job at the wrong minute are others, and the defence is the same — measure on a machine
you have made quiet, and record what quiet meant. Problem 24.4 is to reproduce this on your own
board, where the numbers will differ and the shape should not.

## What we measured

The cost and resolution of the clock; the spread of two thousand runs of one fixed workload — a
body a rounding error wide, and a tail that is all interference; a memory walk run three times with
its data deliberately moved to a different address each time, which on this machine did not move the
time at all; and that same workload with the radio off and on, which moved the mean and left the
floor exactly where it was.

## What this cannot tell you

**Whether your machine behaves like this one.** Almost everything above is a property of a
particular board, a particular kernel and a particular thermal design. The *method* is what
transfers, which is the reason this chapter comes before any result.

**How much repetition is enough.** Problem 24.2 gives the arithmetic for making the clock
negligible, and that is a necessary condition rather than a sufficient one. How many samples you
need before the distribution is trustworthy is a question about the distribution's shape, which
you do not know until you have sampled it.

**What to do about a bimodal result.** Sometimes a benchmark genuinely has two answers — one where
the data was resident and one where it was not — and every summary statistic in this chapter
reports something that happened in neither case. When the histogram has two humps, the right
answer is to find out what distinguishes them, which is [ch30](#whole-machine-profiling)'s equipment.

**Anything about the compiler having deleted your benchmark.** The loop measured here is written
so it cannot be optimised away, and the technique — a dependent chain feeding a value the program
later uses — is stated rather than demonstrated. [ch26](#optimising-code) shows what happens when it is
forgotten, which is a benchmark that measures an empty loop and reports an enormous speedup.

## Problems

Four. The first three are in `tests/measuring/measuring.c` and are graded against definitions the tests
compute for themselves. The fourth has no test: its answer is a property of your machine, not this one's.

**24.1 — Report the distribution.**
Minimum, median, 90th percentile and mean, to the definitions in the stub. The even-length case is
the one that matters: the median of an even set is a sample that happened, not the average of two
that did.

```bash
python3 -m pytest tests/measuring/test_problem_1_summary.py
```

**24.2 — How many repetitions?**
Given what the work costs and what the clock costs, the smallest count for which the instrument is
within budget. One of the cases has the answer "one", and one has the answer "this is not a
question", and both are worth getting right.

```bash
python3 -m pytest tests/measuring/test_problem_2_repetitions.py
```

**24.3 — How much of this is warm-up?**
The definition has two clauses, and the second is where the difficulty is: the prefix you discard
has to have actually been slow. Leave it out and a single spike in the middle lets you throw away
every good measurement before it.

```bash
python3 -m pytest tests/measuring/test_problem_3_warmup.py
```

**24.4 — Reproduce the interference on your own machine.**
The table above is this board's. `python3 -m bench.run_interference` runs the same experiment — it
toggles the radio for you and restores it — so run it on yours and report the three things the
method should let you defend: that the floor did not move, that the mean did, and how often a run
was disturbed. That last figure travels least of anything in this chapter, because it depends on
your radio, your kernel and whatever else the machine was doing — which is why you have to take it
yourself.

There is no test, because the answer is a property of your machine rather than a fact to check
against. If the floor *does* move on yours, something more interesting than the radio is loose, and
tracking it down is the skill this chapter exists to teach.

## Where to go next

Mytkowicz, Diwan, Hauswirth and Sweeney @mytkowicz2009wrong is four pages and is the single most
useful thing to read after this chapter. The experiment is simple enough to repeat and the result
is bad enough to change your habits.

`man 2 clock_gettime` and `man 7 vdso` are worth twenty minutes: the reason reading the clock is
as cheap as it is, on Linux, is that it usually is not a system call at all — [ch16](#traps-and-system-calls)'s trap
path is avoided by mapping a page of kernel data into every process, which is [ch17](#virtual-memory)'s
mechanism used for something [ch17](#virtual-memory) had no reason to mention.

[ch25](#the-memory-hierarchy) is the first chapter to ask the machine a question, and it settles this book's
running example: [ch23](#the-same-program-on-both-targets)'s two routes differ because of where the data
is, and the next chapter measures that hierarchy rather than looking it up.
