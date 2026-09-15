/* See sysfs/include/sysfs/timing.h.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/timing.h"

#include <stdlib.h>
#include <time.h>

#define CLOCK_SAMPLES 1024

uint64_t sysfs_now_ns(void) {
  struct timespec ts;

  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static int compare(const void *a, const void *b) {
  uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
  return (x > y) - (x < y);
}

uint64_t sysfs_clock_cost_ns(void) {
  uint64_t samples[CLOCK_SAMPLES];

  /* Back-to-back reads. The difference between two consecutive readings is one read's cost plus
   * whatever the machine did in between, so the minimum over many is the closest thing available
   * to the cost alone. */
  for (int i = 0; i < CLOCK_SAMPLES; i++) {
    uint64_t before = sysfs_now_ns();
    uint64_t after = sysfs_now_ns();
    samples[i] = after - before;
  }
  qsort(samples, CLOCK_SAMPLES, sizeof(samples[0]), compare);
  return samples[0];
}

struct sysfs_summary sysfs_summarise(uint64_t *samples, uint64_t count) {
  struct sysfs_summary out = {0, 0, 0, 0, 0, 0};

  if (count == 0)
    return out;

  qsort(samples, count, sizeof(samples[0]), compare);

  unsigned __int128 total = 0;
  for (uint64_t i = 0; i < count; i++)
    total += samples[i];

  out.count = count;
  out.min = samples[0];
  out.median = samples[count / 2];
  out.p90 = samples[(count * 9) / 10 < count ? (count * 9) / 10 : count - 1];
  out.max = samples[count - 1];
  out.mean = (uint64_t)(total / count);
  return out;
}
