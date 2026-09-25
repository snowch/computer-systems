/* Running a workload many times and keeping every sample, which is what the book prints from.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * `timing.h` provides the clock and summarises a run in C. That was enough while a figure was a
 * median and a tail. It is not enough for a figure that carries a confidence interval, because an
 * interval is computed from the samples and the samples were thrown away as soon as they were
 * summarised — so a result could never be re-analysed, only re-measured, and re-measuring needs
 * the board.
 *
 * So this keeps them, and writes them out. Everything else follows from that one decision.
 *
 * It reads the clock through `sysfs_now_ns` and nothing else. A harness with its own idea of what
 * time it is would be a second instrument, unexamined, and the measurement chapter would then be
 * arguing about one clock while Part V was timed by another.
 *
 * **Nothing here has a default.** How many times to warm up, how many times to run, and whether
 * the caches should be cold are the three decisions that change what a measurement means, and a
 * harness that chose them quietly would be making the reader's argument for them. Every one is
 * required on the command line, and a workload that omits one does not run.
 */

#ifndef SYSFS_DISTRIBUTION_H
#define SYSFS_DISTRIBUTION_H

#include <stddef.h>
#include <stdint.h>

/* How a run was asked for. Every field is supplied; none is inferred. */
struct sysfs_run_spec {
  uint64_t warmup_runs; /* discarded before any sample is kept */
  uint64_t runs;        /* samples actually recorded */
  int cold;             /* 1 to evict the caches before every sample, 0 to leave them warm */
  const char *raw_path; /* where the samples are written, one per line */
};

/* Parse `--warmup N --runs N --mode cold|warm --raw PATH` and refuse anything less.
 *
 * Returns 0 on success. On failure it prints what was missing and returns non-zero, because the
 * alternative — filling in a default — produces a measurement whose conditions nobody chose.
 */
int sysfs_parse_run_spec(int argc, char **argv, struct sysfs_run_spec *out);

/* Touch enough memory to push this workload's data out of every cache level.
 *
 * "Cold" and "warm" are two different experiments, not one experiment with noise in it, and this
 * is the line between them. It cannot evict what the kernel holds — dropping the page cache needs
 * privileges a benchmark should not have — so the runner does that side, and records whether it
 * managed to.
 */
void sysfs_evict_caches(void);

/* Write `count` samples to `path`, one nanosecond value per line.
 *
 * Raw values, never a summary: a summary is one reading of the samples, and the whole argument of
 * the measurement chapter is that a second reading of the same samples can disagree with the
 * first. Returns 0 on success.
 */
int sysfs_write_samples(const char *path, const uint64_t *samples, uint64_t count);

/* Run `work` under `spec`, keeping every sample, and write them out.
 *
 * `work` is called with `context` and returns nothing; it is timed around. Allocation of the
 * sample array is this function's business, so a workload cannot accidentally keep fewer samples
 * than it ran. Returns 0 on success.
 */
int sysfs_run_distribution(const struct sysfs_run_spec *spec, void (*work)(void *),
                           void *context);

#endif /* SYSFS_DISTRIBUTION_H */
