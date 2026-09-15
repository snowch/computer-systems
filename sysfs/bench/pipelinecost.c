/* pipelinecost — what the core does between fetching an instruction and finishing it.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   pipelinecost chain <n>    sum with n independent accumulators
 *   pipelinecost branch <pct> count the values over a threshold, pct of them predictably
 *
 * One variant per invocation, deliberately. The runner wraps each in `perf stat`, and a process
 * that ran all of them would give one set of counters covering all of them — which is a fair
 * description of nothing.
 *
 * The chain variants do identical arithmetic and differ only in how many additions can be in
 * flight at once. The branch variant does identical arithmetic on data that differs only in how
 * predictable it is.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/pipeline.h"
#include "sysfs/timing.h"

#define COUNT 200000
#define RUNS 100
#define THRESHOLD 512

static long values[COUNT];
static uint64_t samples[RUNS];

/* Same values, different order.
 *
 * The array starts alternating side of the threshold — a period-two pattern any predictor learns
 * — and then `100 - predictable` per cent of the positions are swapped with a random later one.
 * That leaves the multiset untouched, so every predictability level counts exactly the same
 * number of elements and does exactly the same arithmetic. Only the *pattern* differs, which is
 * the one thing a predictor can see.
 *
 * Generating fresh random values per level instead would have changed the answer along with the
 * order, and a comparison between two different workloads is not a comparison.
 */
static uint64_t state = 0x9e3779b97f4a7c15ULL;

static uint64_t next_random(void) {
  state ^= state << 13;
  state ^= state >> 7;
  state ^= state << 17;
  return state;
}

static void fill(int predictable) {
  state = 0x9e3779b97f4a7c15ULL;
  for (long i = 0; i < COUNT; i++)
    values[i] = (i % 2) ? THRESHOLD + 1 : THRESHOLD - 1;
  for (long i = 0; i < COUNT; i++) {
    if ((int)(next_random() % 100) < predictable)
      continue;
    long j = i + (long)(next_random() % (uint64_t)(COUNT - i));
    long swap = values[i];
    values[i] = values[j];
    values[j] = swap;
  }
}

int main(int argc, char **argv) {
  const char *what = argc > 1 ? argv[1] : "chain";
  long parameter = argc > 2 ? strtol(argv[2], NULL, 10) : 1;

  long answer = 0;
  const char *label = "";
  printf("pipelinecost elements %d\n", COUNT);

  if (strcmp(what, "chain") == 0) {
    long (*variant)(const long *, long) = sysfs_sum_chain1;
    switch (parameter) {
    case 2:
      variant = sysfs_sum_chain2;
      label = "sysfs_sum_chain2";
      break;
    case 4:
      variant = sysfs_sum_chain4;
      label = "sysfs_sum_chain4";
      break;
    case 8:
      variant = sysfs_sum_chain8;
      label = "sysfs_sum_chain8";
      break;
    default:
      label = "sysfs_sum_chain1";
      break;
    }
    for (long i = 0; i < COUNT; i++)
      values[i] = i % 97;
    for (int i = 0; i < RUNS; i++) {
      uint64_t before = sysfs_now_ns();
      answer = variant(values, COUNT);
      samples[i] = sysfs_now_ns() - before;
    }
    printf("chain %s total_ns %llu answer %ld\n", label,
           (unsigned long long)sysfs_summarise(samples, RUNS).min, answer);
  } else if (strcmp(what, "branch") == 0) {
    fill((int)parameter);
    for (int i = 0; i < RUNS; i++) {
      uint64_t before = sysfs_now_ns();
      /* The *calling* variant, deliberately. ch19 shows the compiler turning the plain one
       * into a `cset` with no branch in it at all, and a branchless loop cannot mispredict. */
      answer = sysfs_count_over_calling(values, COUNT, THRESHOLD);
      samples[i] = sysfs_now_ns() - before;
    }
    printf("branch predictable %ld total_ns %llu answer %ld\n", parameter,
           (unsigned long long)sysfs_summarise(samples, RUNS).min, answer);
  } else {
    fprintf(stderr, "usage: pipelinecost chain 1|2|4|8 | branch <percent>\n");
    return 2;
  }
  printf("end pipelinecost\n");
  return 0;
}
