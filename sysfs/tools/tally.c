/* tally — the program chapter 20 profiles, and the census that predicts what it will find.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Run with no arguments it does the work and prints a checksum, which is the form the reader
 * profiles. Run with `census` it prints what it is about to do, counted rather than timed: how
 * many records, how wide the table is, how much of it each arrangement touches at once, and how
 * often the conditional in the phase that looks expensive is taken.
 *
 * Every figure in the census is a property of the program and its sizes, so it is the same on any
 * machine and CI can regenerate it. That is the point of it being here: the census is a
 * *prediction*, written down before the profile exists, and ch22 is about the difference.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/profiling.h"

#define RECORDS (1u << 20)
#define ENTRIES (1u << 20)
#define BUCKETS 128u
#define SEED 0x5eed1234u

static uint32_t raw[RECORDS];
static uint32_t keys[RECORDS];
static uint32_t scratch[RECORDS];
static uint32_t table[ENTRIES];
static uint32_t offsets[BUCKETS + 1];

/* How many distinct cache lines of the table the keys reach, counted exactly rather than
 * estimated. A line here is SYSFS_TALLY_LINE bytes wide, so it holds SYSFS_TALLY_PER_LINE
 * counters, and two keys that land in the same line cost one miss between them rather than two. */
static uint64_t distinct_lines(const uint32_t *k, uint64_t n, uint32_t entries) {
  uint64_t lines = (entries + SYSFS_TALLY_PER_LINE - 1) / SYSFS_TALLY_PER_LINE;
  unsigned char *seen = calloc(lines, 1);
  if (!seen)
    return 0;
  uint64_t touched = 0;
  for (uint64_t i = 0; i < n; i++) {
    uint64_t line = k[i] / SYSFS_TALLY_PER_LINE;
    if (!seen[line]) {
      seen[line] = 1;
      touched++;
    }
  }
  free(seen);
  return touched;
}

static uint64_t distinct_keys(const uint32_t *k, uint64_t n, uint32_t entries) {
  unsigned char *seen = calloc(entries, 1);
  if (!seen)
    return 0;
  uint64_t distinct = 0;
  for (uint64_t i = 0; i < n; i++)
    if (!seen[k[i]]) {
      seen[k[i]] = 1;
      distinct++;
    }
  free(seen);
  return distinct;
}

/* How many times to repeat one arrangement when it is being profiled. A sampling profiler needs
 * the program to run long enough to collect samples, and one pass of this is over in a moment. */
#define PROFILE_PASSES 40

int main(int argc, char **argv) {
  const char *mode = argc > 1 ? argv[1] : "";
  int census = strcmp(mode, "census") == 0;

  sysfs_tally_fill(SEED, raw, RECORDS);
  uint64_t taken = sysfs_tally_decode(raw, RECORDS, keys, ENTRIES);

  /* One arrangement at a time, for ch22's before-and-after profiles. A process that ran both
   * would give one profile covering both, which is a fair description of neither. */
  if (strcmp(mode, "scatter") == 0 || strcmp(mode, "partitioned") == 0) {
    uint64_t sum = 0;
    for (int pass = 0; pass < PROFILE_PASSES; pass++)
      sum += strcmp(mode, "scatter") == 0
                 ? sysfs_tally_scatter(keys, RECORDS, table, ENTRIES)
                 : sysfs_tally_partitioned(keys, RECORDS, table, ENTRIES, BUCKETS, scratch,
                                           offsets);
    printf("tally %s %llu passes %d\n", mode, (unsigned long long)sum, PROFILE_PASSES);
    return 0;
  }

  uint64_t scattered = sysfs_tally_scatter(keys, RECORDS, table, ENTRIES);
  uint64_t partitioned =
      sysfs_tally_partitioned(keys, RECORDS, table, ENTRIES, BUCKETS, scratch, offsets);

  if (!census) {
    printf("tally %llu\n", (unsigned long long)scattered);
    return scattered == partitioned ? 0 : 1;
  }

  uint32_t slice = ENTRIES / BUCKETS;
  printf("tally records %u entries %u line_bytes %u\n", RECORDS, ENTRIES, SYSFS_TALLY_LINE);
  printf("tally table_bytes %zu slice_bytes %zu\n", (size_t)ENTRIES * sizeof(uint32_t),
         (size_t)slice * sizeof(uint32_t));
  printf("tally decode taken %llu of %u\n", (unsigned long long)taken, RECORDS);
  printf("tally scatter distinct_keys %llu lines %llu\n",
         (unsigned long long)distinct_keys(keys, RECORDS, ENTRIES),
         (unsigned long long)distinct_lines(keys, RECORDS, ENTRIES));
  printf("tally partitioned buckets %u slice_entries %u key_reads %llu key_writes %llu\n", BUCKETS,
         slice, (unsigned long long)RECORDS * 3, (unsigned long long)RECORDS);
  printf("tally checksum scatter %llu partitioned %llu agree %s\n",
         (unsigned long long)scattered, (unsigned long long)partitioned,
         scattered == partitioned ? "yes" : "no");
  printf("end tally\n");
  return 0;
}
