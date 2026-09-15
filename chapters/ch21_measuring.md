---
title: "Measuring"
short_title: "ch21 Measuring"
---

(ch21)=
# ch21 · Measuring

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — the reference machine, natively |
| **Prerequisites** | [ch20](#ch20) |
| **What it measures** | The instrument, before anything is measured with it: `bench/results/measuring-host.json` |
:::

## The question

How do I get a number I would defend, and how would I know it was wrong?

[ch20](#ch20) established that the structural model does not predict cost, and pointed at a
machine that can answer. Before asking it anything, this chapter asks what it costs to ask — and
then arranges, deliberately, for the same program to give three different answers.

## The material

### The instrument is part of the measurement

Every duration in this book is read through one header, so that "how was this timed" has one
answer rather than one per chapter:

```{literalinclude} ../sysfs/include/sysfs/timing.h
:language: c
:start-at: uint64_t sysfs_now_ns(void);
:end-before: /* The distribution
```

The second function is the one people skip. Reading a clock takes time, that time is included in
every measurement made with it, and if the thing being measured is of the same order then the
instrument is most of what is being measured.

```{include} _generated/ch21-clock.md
```

Two numbers there, and they are not the same question. What a clock *costs* is how long the read
takes. What it can *resolve* is the smallest change it will ever report — a clock can hand back
nanoseconds and still only ever move in steps of a hundred of them, in which case a measurement of
anything shorter is a coin toss between zero and one step.

Problem 14.2 turns this into the arithmetic you actually need: given what the work costs and what
the clock costs, how many repetitions must go inside one timed region before the instrument is
small enough to ignore.

### There is no such thing as the time it took

Run identical work, on an idle machine, two thousand times:

```{include} _generated/ch21-spread.md
```

The last row is the chapter. Identical work, identical input, nothing else running — and the
slowest run is a multiple of the fastest. Nothing was wrong with any of those measurements; they
are all correct observations of what happened.

So "how long does it take" has no answer, and the question has to be replaced. What is reported
instead is a distribution, which is why `sysfs_summarise` exists and why problem 14.1 asks you to
write it.

**Why the minimum is usually the number to look at.** Everything that can happen to a measurement
on a real machine makes it slower: an interrupt arrives, another process is scheduled, a page is
not resident, the clock drifts. Almost nothing makes it faster. So the mean is partly a statement
about the interference and the minimum is the closest available statement about the work.

**And when that reasoning fails.** If you care how long something takes *in service*, the
interference is not noise — it is the thing your users experience, and reporting the minimum is
reporting the one case that never happens to them. Two different questions, two different
statistics, and the mistake is not picking the wrong one but not noticing there was a choice.

### Warming up is not a ritual

The first few measurements are slower, always, and for reasons Parts III and IV have already
explained: [ch15](#ch15)'s pages are not yet faulted in, [ch22](#ch22)'s caches hold somebody
else's data, and the branch predictor of [ch24](#ch24) has never seen this loop.

Discarding them is standard practice and is usually done wrong. Warm-up is a property of
*position*: the first samples are slow because they are first. A slow sample in the middle is
interference, it is not warm-up, and discarding everything before it throws away good
measurements in order to hide a bad one. Problem 14.3 is exactly that distinction, and the
definition it asks you to implement has a second clause for no other reason.

### The same program, three answers

Here is the experiment that should change how you read a benchmark.

The same work, the same input, the same binary, three times — differing only in how many bytes of
stack were claimed before the loop ran. Not used. Claimed.

```{include} _generated/ch21-bias.md
```

Nothing about the work changed. What changed is where everything landed in memory, and therefore
which cache sets the data occupied, and therefore how often two things that are used together
evicted each other.

This is measurement bias, and Mytkowicz and colleagues @mytkowicz2009wrong showed it is large
enough to manufacture or erase the kind of speedup papers are published about — by changing the
size of an environment variable, which moves the stack, which does exactly what the padding above
does. Their conclusion is the uncomfortable one: a single configuration, measured carefully, can
give a confidently wrong answer, and no amount of repetition inside that configuration finds it.

The defence is to vary the thing that should not matter, on purpose, and see whether your result
survives.

### The floor moves

One more, specific to this book's reference machine and to most small ones.

A Raspberry Pi 5 under sustained load gets hot and reduces its clock. Not gradually and not with a
warning: the frequency drops, and every measurement after that point is against a different
machine from the ones before it. A benchmark that runs for a minute can therefore show a
"regression" in its second half that is entirely thermal — and a comparison between two
implementations, run one after the other, can rank them by which went first.

The defence is to record the clock alongside the result, which is why [ch00](#ch00) insists on the
active cooler and why every `host` result in this book stamps the machine's state as well as its
number. It is also why the results are taken with the board idle and the laptop not driving it
over a link that interrupts it, which brings up something the book has to admit.

### A claim this book has not measured

[ch00](#ch00) recommends wiring the board rather than using its radio, and gives a mechanism: a
wireless driver takes interrupts and runs deferred work on the cores being measured, which is
[ch16](#ch16)'s subject arriving where it is least wanted.

The mechanism is real. The effect on these measurements has never been measured, and ch00 says so.
That is an unmeasured claim about hardware behaviour in a book whose whole discipline is refusing
them, and the honest thing to do with it is to hand it to the reader: it is the fourth problem
below, the answer is genuinely unknown to the author, and a reader who falsifies it has exactly
the skill this chapter exists to teach.

## What we measured

The cost and resolution of the clock; the distribution of two thousand runs of one fixed workload;
and the same workload three times with a variable changed that cannot affect it.

All three are declared pending until `make bench-board` runs on the reference machine, which is
the only place this book takes a duration. The prose is written for the numbers rather than around
them: landing them is one command.

## What this cannot tell you

**Whether your machine behaves like this one.** Almost everything above is a property of a
particular board, a particular kernel and a particular thermal design. The *method* is what
transfers, which is the reason this chapter comes before any result.

**How much repetition is enough.** Problem 14.2 gives the arithmetic for making the clock
negligible, and that is a necessary condition rather than a sufficient one. How many samples you
need before the distribution is trustworthy is a question about the distribution's shape, which
you do not know until you have sampled it.

**What to do about a bimodal result.** Sometimes a benchmark genuinely has two answers — one where
the data was resident and one where it was not — and every summary statistic in this chapter
reports something that happened in neither case. When the histogram has two humps, the right
answer is to find out what distinguishes them, which is [ch27](#ch27)'s equipment.

**Anything about the compiler having deleted your benchmark.** The loop measured here is written
so it cannot be optimised away, and the technique — a dependent chain feeding a value the program
later uses — is stated rather than demonstrated. [ch23](#ch23) shows what happens when it is
forgotten, which is a benchmark that measures an empty loop and reports an enormous speedup.

## Problems

Four. The first three are in `tests/ch21/measuring.c` and are graded against definitions the tests
compute for themselves. The fourth has no test and no known answer.

**14.1 — Report the distribution.**
Minimum, median, 90th percentile and mean, to the definitions in the stub. The even-length case is
the one that matters: the median of an even set is a sample that happened, not the average of two
that did.

```bash
python3 -m pytest tests/ch21/test_problem_1_summary.py
```

**14.2 — How many repetitions?**
Given what the work costs and what the clock costs, the smallest count for which the instrument is
within budget. One of the cases has the answer "one", and one has the answer "this is not a
question", and both are worth getting right.

```bash
python3 -m pytest tests/ch21/test_problem_2_repetitions.py
```

**14.3 — How much of this is warm-up?**
The definition has two clauses and the second is the whole problem: the prefix you discard has to
have actually been slow. Leave it out and a single spike in the middle lets you throw away every
good measurement before it.

```bash
python3 -m pytest tests/ch21/test_problem_3_warmup.py
```

**14.4 — Falsify something this book says.**
[ch00](#ch00) claims that a wireless link adds interrupt and deferred work to the cores being
measured, and admits it has not measured the effect. Measure it: run one of this chapter's
workloads with the board on Ethernet and on its radio, with and without traffic, and report
whether the distributions differ in a way the method above would defend.

There is no test, because there is no answer to check against. If you find the claim is
unsupported at the scale this book's measurements work at, [ch00](#ch00) is wrong and should say
something else — and a reader who establishes that has done the thing this chapter is for.

## Where to go next

Mytkowicz, Diwan, Hauswirth and Sweeney @mytkowicz2009wrong is four pages and is the single most
useful thing to read after this chapter. The experiment is simple enough to repeat and the result
is bad enough to change your habits.

`man 2 clock_gettime` and `man 7 vdso` are worth twenty minutes: the reason reading the clock is
as cheap as it is, on Linux, is that it usually is not a system call at all — [ch13](#ch13)'s trap
path is avoided by mapping a page of kernel data into every process, which is [ch14](#ch14)'s
mechanism used for something [ch14](#ch14) had no reason to mention.

[ch22](#ch22) is the first chapter to ask the machine a question, and it is the one this book's
running example has been waiting for: [ch20](#ch20)'s two routes differ because of where the data
is, and the next chapter measures that hierarchy rather than looking it up.
