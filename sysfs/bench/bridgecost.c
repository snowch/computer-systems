/* bridgecost — what the two routes actually cost, on the machine being measured.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The same two functions the xv6 half runs for its answers, timed here for its price. Both walk
 * the same cells and compute the same total; one walks them in address order and the other
 * follows a pointer from each to the next, so the machine cannot know where the next one is until
 * the current load has returned.
 *
 * Reports the minimum of many runs, for the reason the measurement chapter gives: everything that can happen to a
 * measurement on a real machine makes it slower and nothing makes it faster.
 */

#include <stdio.h>
#include <stdlib.h>

#include "sysfs/bridge.h"
#include "sysfs/timing.h"

SYSFS_BRIDGE_DEFINE

#define CELLS 4096
#define RUNS 200

static struct sysfs_cell cells[CELLS];
static uint64_t samples[RUNS];

static uint64_t time_route(long (*route)(const struct sysfs_cell *, long), long *answer) {
  for (int i = 0; i < RUNS; i++) {
    uint64_t before = sysfs_now_ns();
    *answer = route(cells, CELLS);
    samples[i] = sysfs_now_ns() - before;
  }
  return sysfs_summarise(samples, RUNS).min;
}

int main(void) {
  long stride = sysfs_bridge_stride(CELLS);
  sysfs_bridge_fill(cells, CELLS, stride);

  long sequential_answer = 0, chased_answer = 0;
  uint64_t sequential = time_route(sysfs_bridge_sequential, &sequential_answer);
  uint64_t chased = time_route(sysfs_bridge_chased, &chased_answer);

  printf("bridge cells %d stride %ld\n", CELLS, stride);
  printf("bridge agree %s\n", sequential_answer == chased_answer ? "yes" : "no");
  printf("bridge sequential_ns %llu chased_ns %llu\n", (unsigned long long)sequential,
         (unsigned long long)chased);
  printf("end bridgecost\n");
  return 0;
}
