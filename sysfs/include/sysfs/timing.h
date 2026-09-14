/* The book's clock, and the honesty about it that chapter 14 is for.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Every duration in Part III is read through this header, so that "how was this timed" has one
 * answer rather than one per chapter. Three things it deliberately provides and one it
 * deliberately does not.
 *
 * It provides a clock, the cost of reading that clock, and a way to run something many times and
 * report the distribution rather than a number. The last of those is the one that matters: a
 * single duration is not a measurement, it is an anecdote, and the whole of ch14 is about what to
 * report instead.
 *
 * It does not provide a "benchmark this function" macro. Deciding what to repeat, what to warm up
 * and what to report is the skill the chapter teaches, and a macro that made those decisions
 * invisibly would remove exactly the thing the reader came for.
 */

#ifndef SYSFS_TIMING_H
#define SYSFS_TIMING_H

#include <stdint.h>

/* Nanoseconds from a monotonic clock — one that cannot go backwards and is not adjusted by
 * anything that keeps wall-clock time honest. Using a wall clock for a benchmark means a
 * time-synchronisation daemon can make a program appear to run in negative time, which does
 * happen and is memorable. */
uint64_t sysfs_now_ns(void);

/* What reading the clock costs, in nanoseconds, measured by reading it repeatedly.
 *
 * This is not trivia. If a thing being measured is of the same order as the instrument, the
 * instrument is most of what is being measured — and knowing where that threshold is tells you
 * when to stop timing single operations and start timing a loop of them. */
uint64_t sysfs_clock_cost_ns(void);

/* The distribution of a repeated measurement, which is what should be reported instead of a
 * number. `count` samples, in nanoseconds, are summarised. The samples are sorted in place. */
struct sysfs_summary {
  uint64_t count;
  uint64_t min;
  uint64_t median;
  uint64_t p90;
  uint64_t max;
  uint64_t mean;
};

struct sysfs_summary sysfs_summarise(uint64_t *samples, uint64_t count);

/* Why the minimum, and not the mean, is usually the number to look at: everything that can happen
 * to a measurement on a real machine makes it slower, and nothing makes it faster. The mean is
 * therefore a statement about the interference and the minimum is the closest available statement
 * about the work. ch14 says when that reasoning fails. */

#endif /* SYSFS_TIMING_H */
