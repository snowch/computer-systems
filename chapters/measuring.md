---
title: "24 · Measuring"
short_title: "24 · Measuring"
---

(measuring)=
# 24 · Measuring

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `host` — native Linux on real hardware |
| **Prerequisites** | [ch23](#the-same-program-on-both-targets) |
| **Evidence** | Recorded clock and workload timings, plus the planned tests of sample spread and uncertainty. |
:::

## The question

How can you tell whether a measured time reflects the work or the way you measured it?

Use the reference board's recorded runs to learn what the clock costs, how much identical runs
vary, and how a change in the test conditions can affect the result. Then use a rule that
separates sampling uncertainty from the size of a change you care about.

(measuring-example)=
## Compare the instrument, samples and conditions

### The instrument is part of the measurement

The timing code reads a *monotonic clock*, whose reported time cannot go backwards when the
wall clock is set. A clock read also uses time. Compare **Cost of reading the clock** with
**Smallest change the clock ever reports** in the reference result below. The first row measures
overhead. The second shows the smallest step seen during the probe.

```{include} _generated/measuring-clock.md
```

If the work and timer overhead take about as long as each other, the overhead accounts for a
large share of the measured time. Put several repetitions inside one timed region to reduce that
share. Problem 24.2 asks you to choose the smallest repetition count that meets a stated budget.

### The harness costs something as well

The *harness* is the code that runs and times the workload. Time an empty region with the same
harness to estimate how much the harness contributes inside each measured interval. Compare the
**Median** for the empty region and for the workload, then use **The workload, in harnesses**
to see their ratio. The spread from *p5* to *p95* is the difference between the fifth and
ninety-fifth percentiles of the empty-region samples.

```{include} _generated/measuring-harness.md
```

An empty region can have varying costs. Subtracting its median removes an estimated offset and
leaves the variation in the measurements. Design the measured region to take much longer than
the empty region, then confirm the ratio on the machine you use.

(there-is-no-such-thing-as-the-time-it-took)=
### Durations vary across runs

The runner repeated the same work with the same input on the reference board. Compare
**Fastest**, **Median**, **90th percentile** and **Slowest** in the recorded table. Which values
are close together? Which show unusually long runs?

```{include} _generated/measuring-spread.md
```

A real change in scheduling or cache state can make one run slower. The minimum estimates the
fastest observed case under the test conditions. Use a median and spread to describe typical
variation. Include relevant tail percentiles if your question is what users experience during
slow runs.

(why-the-first-measurements-are-slow)=
### Identify warm-up before you discard samples

Early samples can take longer while memory pages become available, caches fill and the branch
predictor learns the loop. Decide whether that start-up cost belongs in the question you are
asking. If you set aside an initial warm-up period to measure steady operation, record how many
samples you discarded. A later spike remains evidence about the measured conditions. Problem
24.3 asks you to distinguish a slow initial segment from an isolated spike.

### Cold and warm are two experiments

Ask how long the same work takes when supporting data is likely to be in cache and when it has
been evicted. The distribution runner accepts an explicit mode. In `cold` mode it runs a cache
eviction pass before each timed sample. In `warm` mode it leaves the cache alone between samples.
The output records the mode and discarded warm-up samples.

Compare **Median**, **p5** and **p95** for each mode once you have the results. Is the difference
between modes larger than the variation within either mode? Eviction changes the starting
condition. It cannot establish that every cache entry was empty.

```{include} _generated/measuring-cold-warm.md
```

(the-variable-that-should-not-matter)=
### Check whether data placement affects the result

The reference runner varied how much stack space it claimed before allocating the buffer. That
changes where the data sits while keeping the work and input fixed. Compare **Fastest** and
**Median** across the three settings. Which statistic moved in these runs?

```{include} _generated/measuring-bias.md
```

The medians match for these runs. A study that varied stack layout found different effects on its
machines @mytkowicz2009wrong. Change a layout-related condition in your own measurements before
assuming its effect is negligible.

(the-floor-moves)=
### Check clock frequency during long runs

Frequency can change if a board heats up under sustained load. If a second version starts on a
hotter board than the first, the result can reflect the temperature difference. Record the
frequency and temperature when available, then check run order before attributing a change to
the code.

(what-else-the-machine-is-doing)=
### Compare quiet and active Wi-Fi

The reference runner does the same work several times with Wi-Fi off and again with it on. A
wireless driver can add activity on the cores running the benchmark. Compare **Fastest sample**,
**Worst run's mean** and **Runs disturbed** in the two columns. Does the fastest sample shift?
Does the worst mean shift in the same way?

```{include} _generated/measuring-interference.md
```

The fastest sample matches and the worst mean rises in the recorded Wi-Fi-on runs. That is an
observation from this board under these conditions. The disturbed-run count uses a threshold
relative to the fastest sample. Problem 24.4 asks you to compare those fields on your machine.

(how-many-runs-is-enough)=
### Estimate how the median varies with sample count

A *bootstrap interval* uses the collected readings to estimate uncertainty in a statistic. Draw
a new sample set of the same size, choosing each reading independently from the observed values.
A reading can appear more than once. Repeat the draw, compute a median each time and use the
middle range of those medians as an interval. This assumes the observations from the run are
exchangeable. Drift or dependent samples can invalidate the estimate.

The runner uses increasingly long prefixes of the same recorded run. Compare **Runs used** and
**Width** to judge whether using more samples noticeably narrows the interval. A narrow interval
can still describe measurements made under systematically different conditions.

```{include} _generated/measuring-runs.md
```

(is-b-faster-than-a)=
### Decide whether a difference is large enough to report

The baseline uses a plain loop. The candidate processes several elements per iteration. Define
the smallest relative difference you care about before you collect results. The runner for
this comparison uses a threshold of two per cent.

Read **Difference** as the candidate median minus the baseline median. Check whether **Interval
on the difference** excludes zero. Then compare **Difference, relative** with **Threshold, fixed
in advance**. When both checks pass, the sign of the difference gives the direction. A negative
difference means the candidate took less time. Otherwise the rule returns **cannot tell**.

```{include} _generated/measuring-verdict.md
```

If the interval includes zero, seek better evidence about direction. If the difference falls
below your chosen threshold, ask whether the size of the change matters for your use. Problem
24.5 asks you to separate these two reasons for the same verdict.

## What we measured

The clock, repeated workload, placement and Wi-Fi tables contain recorded Pi results. The empty
harness, cold/warm, sample-count and loop-comparison figures still need runs on the reference
board. Their pending notes indicate which measurements are missing.

On a board that passes [ch01](#setting-up-the-board), you can run the four pending experiments
from a separate checkout. The command leaves the reference result file untouched and writes
raw readings under `bench/raw/` in that checkout. The cold test uses a cache eviction pass and
attempts to drop the Linux page cache, so run it on a machine set aside for measurements.

```bash
python3 -m bench.run_distribution --check
```

In the terminal JSON, look for `harness`, `plain` and `cold` for the first two comparisons.
Read `narrowing` for sample count and interval width. Read `verdict` for the difference, interval,
threshold and decision. If the runner says the workload is too close to the harness overhead,
make the timed work larger in `sysfs/bench/distcost.c` before interpreting the result.

## What this cannot tell you

**Physical timing under emulation.** QEMU runs instructions on a different executing machine.
Its elapsed time reflects that machine and the translation. The book uses emulated results for
behaviour and native hardware for costs.

**What caused variation.** A long tail can suggest interference. Use additional observations
or a controlled change to identify the source. Warm-up, timing decisions and compiler
optimisation can each alter the result.

**Whether another machine or a live service behaves the same way.** The recorded figures describe
this board and its workload. A service has its own workload and disturbances. A small set of
samples gives little evidence about rare slow requests.

## Problems

Run the test commands from the repository root. The C and Python problems use inputs supplied by
the tests. Only the Wi-Fi experiment requires the reference hardware capabilities.

**24.1 — Report the distribution.**
Open `tests/measuring/measuring.c` and complete `m_summarise`. Use the definitions in the stub
for minimum, median, 90th percentile and mean. The test includes even-length samples, for which
this exercise uses the upper middle sample as its median.

```bash
python3 -m pytest tests/measuring/test_problem_1_summary.py
```

**24.2 — How many repetitions?**
In `tests/measuring/measuring.c`, complete `m_repetitions`. Find the smallest count that keeps
timer overhead within the given budget. Use the stub's return value for an impossible budget.
The test includes work that needs only one repetition.

```bash
python3 -m pytest tests/measuring/test_problem_2_repetitions.py
```

**24.3 — How much of this is warm-up?**
In `tests/measuring/measuring.c`, complete `m_warmup`. Use both conditions in the stub to
choose the number of initial samples to discard. The test includes a spike later in the run.

```bash
python3 -m pytest tests/measuring/test_problem_3_warmup.py
```

**24.4 — Compare Wi-Fi off and on.**
On your native Linux board, connect over Ethernet or use a local terminal. This experiment uses
`sudo nmcli` to turn Wi-Fi off and on and leaves it off at the end. Run from the repository
root with Wi-Fi already configured if you want the on condition to be associated with a network.

```bash
python3 -m bench.run_interference --check
```

The command compares your run with the saved board result and writes no result files. Compare
`quiet` and `radio` for `floor_ns`, `worst_mean_ns` and `disturbed_runs`. A field omitted from
the difference output matched the corresponding saved value. Did Wi-Fi change the floor or the
slow runs more? A reported difference is a finding to interpret. The command uses a nonzero exit
status when a saved value differs. There is no test of your interpretation.

**24.5 — Why did the rule decline to call a winner?**
In `tests/measuring/judging.py`, complete `why_undecided`. Separate a difference whose interval
includes zero from one that falls below the size threshold. Read the failing case to see which
condition the test supplied.

```bash
python3 -m pytest tests/measuring/test_problem_5_verdict.py
```

**24.6 — Is your harness measuring itself?**
In `tests/measuring/judging.py`, complete `reportable`. Use the measured duration and the timer
overhead to decide whether the duration meets the stated multiple of the overhead.

```bash
python3 -m pytest tests/measuring/test_problem_6_floor.py
```

**24.7 — What goes in the result record?**
In `tests/measuring/judging.py`, complete `environment_record`. Use the required field names in
the stub. Include a value of `None` for each field the readings do not supply. The test reports
any missing or mismatched field.

```bash
python3 -m pytest tests/measuring/test_problem_7_stamp.py
```

## Where to go next

Mytkowicz, Diwan, Hauswirth and Sweeney @mytkowicz2009wrong show how changes such as a new stack
layout can shift a benchmark. For Linux's clock implementations, read `man 2 clock_gettime` and
`man 7 vdso`.

Continue to [ch25](#the-memory-hierarchy) and use the measurement method to see how changing the
amount of data affects access time.
