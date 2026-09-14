/* hierarchy — find out where the data is, by asking rather than by reading a datasheet.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   hierarchy sizes     latency against working-set size: the steps are the levels
 *   hierarchy stride    latency against stride: the step is the line size
 *   hierarchy reach     latency against how many pages are touched: the step is the TLB
 *
 * Every experiment is a dependent pointer chase, and that is not decoration. A chase makes each
 * load wait for the one before it, so the machine cannot overlap them and what is measured is one
 * latency rather than a throughput. A loop that walks an array with independent loads measures
 * how many the machine can have in flight at once, which is a real number and a different one.
 *
 * Prints one fact per line, `kind name value`, like every other tool in this book.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/timing.h"

#define REPEATS 16
#define CHASES 2000000
#define MAX_BYTES (64u << 20)

static void **arena;

/* Lay out a cycle through `count` slots `stride` bytes apart, visiting each exactly once. The
 * order is deliberately not sequential: a prefetcher that spots a pattern would answer a
 * different question from the one being asked. */
static void chain(unsigned long count, unsigned long stride_slots) {
  unsigned long step = stride_slots;

  if (step == 0)
    step = 1;
  while (count % step == 0 && step + 1 < count)
    step++;

  unsigned long at = 0;
  for (unsigned long i = 0; i < count; i++) {
    unsigned long next = (at + step) % count;
    arena[at * stride_slots] = &arena[next * stride_slots];
    at = next;
  }
}

static uint64_t chase(unsigned long chases) {
  uint64_t best = 0;

  for (int r = 0; r < REPEATS; r++) {
    void **p = &arena[0];
    uint64_t before = sysfs_now_ns();
    for (unsigned long i = 0; i < chases; i++)
      p = (void **)*p;
    uint64_t after = sysfs_now_ns();
    if (p == NULL)
      printf("unreachable\n");
    uint64_t each = (after - before) / chases;
    if (best == 0 || each < best)
      best = each;
  }
  return best;
}

int main(int argc, char **argv) {
  const char *what = argc > 1 ? argv[1] : "sizes";

  arena = malloc(MAX_BYTES);
  if (arena == NULL) {
    fprintf(stderr, "hierarchy: cannot allocate %u bytes\n", MAX_BYTES);
    return 1;
  }
  memset(arena, 0, MAX_BYTES);

  printf("hierarchy 1\n");
  printf("clock cost_ns %llu\n", (unsigned long long)sysfs_clock_cost_ns());

  if (strcmp(what, "sizes") == 0) {
    /* One slot per cache line's worth of stride, so each visit is a new line and the only thing
     * varying is how much memory the cycle covers. */
    unsigned long stride_slots = 8; /* 64 bytes, checked by the stride experiment */
    for (unsigned long bytes = 1024; bytes <= MAX_BYTES; bytes *= 2) {
      unsigned long count = bytes / (stride_slots * sizeof(void *));
      if (count < 2)
        continue;
      chain(count, stride_slots);
      printf("size bytes %lu ns %llu\n", bytes, (unsigned long long)chase(CHASES));
    }
  } else if (strcmp(what, "stride") == 0) {
    /* A fixed number of visits over a fixed span, with the gap between them growing. The step is
     * where consecutive visits stop sharing a line. */
    for (unsigned long stride = 8; stride <= 4096; stride *= 2) {
      unsigned long slots = stride / sizeof(void *);
      unsigned long count = 4096;
      chain(count, slots);
      printf("stride bytes %lu ns %llu\n", stride, (unsigned long long)chase(CHASES));
    }
  } else if (strcmp(what, "reach") == 0) {
    /* One visit per page, so the data fits in cache long after the translations do not. What
     * moves is how many pages the walk touches, and the step is the reach of the TLB. */
    unsigned long page = 4096;
    for (unsigned long pages = 4; pages <= MAX_BYTES / page; pages *= 2) {
      chain(pages, page / sizeof(void *));
      printf("reach pages %lu ns %llu\n", pages, (unsigned long long)chase(CHASES));
    }
  } else {
    fprintf(stderr, "usage: hierarchy sizes|stride|reach\n");
    return 2;
  }
  printf("end hierarchy\n");
  free(arena);
  return 0;
}
