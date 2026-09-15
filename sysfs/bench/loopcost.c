/* loopcost — what chapter 18's five hand-optimisations cost, on the machine being measured.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Five spellings of one loop, each computing the same total. The chapter's question is what the
 * differences between them are worth once a compiler has had them, and the answer needs a clock.
 *
 * Reports nanoseconds per element so the five are comparable, and the minimum of many runs.
 */

#include <stdio.h>
#include <stdlib.h>

#include "sysfs/loops.h"
#include "sysfs/timing.h"

#define COUNT 100000
#define RUNS 200
#define SCALE 3

static long values[COUNT];
static uint64_t samples[RUNS];

/* Returns the whole sweep, not a per-element figure. Dividing here would floor a sub-nanosecond
 * cost to zero — which it does, at this element count on this machine — and the runner can keep
 * the precision that C's integer division throws away. */
static uint64_t sweep_ns(long (*variant)(const long *, long, long), long *answer) {
  for (int i = 0; i < RUNS; i++) {
    uint64_t before = sysfs_now_ns();
    *answer = variant(values, COUNT, SCALE);
    samples[i] = sysfs_now_ns() - before;
  }
  return sysfs_summarise(samples, RUNS).min;
}

int main(void) {
  for (long i = 0; i < COUNT; i++)
    values[i] = (i * 2654435761u) % 1024;

  struct {
    const char *name;
    long (*fn)(const long *, long, long);
  } variants[] = {
      {"plain", sysfs_loop_plain},         {"hoisted", sysfs_loop_hoisted},
      {"reduced", sysfs_loop_reduced},     {"unrolled", sysfs_loop_unrolled},
      {"everything", sysfs_loop_everything},
  };

  printf("loopcost elements %d\n", COUNT);
  long first = 0;
  for (unsigned i = 0; i < sizeof variants / sizeof variants[0]; i++) {
    long answer = 0;
    uint64_t ns = sweep_ns(variants[i].fn, &answer);
    if (i == 0)
      first = answer;
    printf("loop %s total_ns %llu agrees %s\n", variants[i].name, (unsigned long long)ns,
           answer == first ? "yes" : "no");
  }
  printf("end loopcost\n");
  return 0;
}
