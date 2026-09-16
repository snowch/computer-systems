/* The program the profiling chapter hands the reader without explaining it.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Everything measured up to here has been code this book wrote, in a loop chosen to isolate one
 * mechanism, with the answer already known. That is the wrong shape for the skill the profiling chapter is about,
 * which is finding the expensive part of something nobody explained to you.
 *
 * So: three phases over a stream of records, one of which dominates. The header says what each
 * phase does and deliberately does not say which one that is — the chapter's whole argument is
 * that reading the source is not how you find out.
 */

#ifndef SYSFS_PROFILING_H
#define SYSFS_PROFILING_H

#include <stdint.h>

/* The table's entries are counters, and a cache line holds this many of them. Named here because
 * the census in `bench/run_profile.py` counts lines rather than bytes, and a count of lines is
 * only meaningful beside the width that produced it. */
#define SYSFS_TALLY_LINE 64u
#define SYSFS_TALLY_PER_LINE (SYSFS_TALLY_LINE / sizeof(uint32_t))

/* Phase one. Fill `raw` with `n` deterministic records from `seed`. The generator is an xorshift,
 * so the same seed gives the same stream on every machine and the census below is a property of
 * the program rather than of the run. */
void sysfs_tally_fill(uint64_t seed, uint32_t *raw, uint64_t n);

/* Phase two. Turn each record into a table index below `entries`, writing them to `keys`.
 *
 * This is the phase that looks expensive: a shift, a multiply, a conditional. Returns how many
 * times the conditional was taken, which is the only thing about this function worth knowing
 * before the profile arrives. */
uint64_t sysfs_tally_decode(const uint32_t *raw, uint64_t n, uint32_t *keys, uint32_t entries);

/* Phase three, first arrangement. One increment per key, in the order the keys arrive.
 *
 * Returns a checksum, so that nothing here can be optimised away and the two arrangements can be
 * required to agree. */
uint64_t sysfs_tally_scatter(const uint32_t *keys, uint64_t n, uint32_t *table, uint32_t entries);

/* Phase three, second arrangement. The same increments and the same answer, reached by sorting
 * the keys into `buckets` runs first and tallying one run at a time, so that every increment lands
 * in a slice of the table small enough to stay put.
 *
 * It is strictly more work: the keys are read twice more and written once more, and `scratch`
 * must hold `n` of them while `offsets` holds `buckets + 1`. `entries` must divide evenly by
 * `buckets`. Whether trading that work for locality pays is not something this header knows, and
 * the chapter does not assume it.
 *
 * Returns the same checksum as the first arrangement, which the census requires. */
uint64_t sysfs_tally_partitioned(const uint32_t *keys, uint64_t n, uint32_t *table,
                                 uint32_t entries, uint32_t buckets, uint32_t *scratch,
                                 uint32_t *offsets);

#endif /* SYSFS_PROFILING_H */
