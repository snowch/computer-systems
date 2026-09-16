/* measuring — the three experiments the measurement chapter is about, on the machine itself.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   measuring clock        what reading the clock costs, and what it can resolve
 *   measuring spread       one fixed workload, many times, reported as a distribution
 *   measuring bias         the same workload, its data placed differently each time by a
 *                          variable that changes nothing about the computation
 *
 * Prints one fact per line, `kind name value`, like every other tool in this book. It takes no
 * decisions about what to report: that is the reader's job and the chapter's subject. In
 * particular it does not decide whether the bias experiment found an effect. It reports the three
 * runs and the address the data actually landed at each time, and the chapter reads them.
 */

#include <alloca.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/timing.h"

#define SAMPLES 2000
#define WORK 20000

/* The bias experiment's working set: larger than this core's L1, so the dependent walk over it is
 * decided by where the data landed rather than by throughput. */
#define CHASE_SLOTS (20u * 1024u) /* 20K slots * 8 bytes = 160 KiB */
#define CHASE_STRIDE 512u         /* elements between links: 512 * 8 = 4096 bytes */
#define CHASE_ROUNDS 6

static uint64_t samples[SAMPLES];

/* The thing measured by clock and spread: deliberately small, deliberately dependent, and
 * deliberately unoptimisable, so that the compiler cannot delete it and the machine cannot overlap
 * it. */
static uint64_t chew(uint64_t seed, unsigned long rounds) {
  for (unsigned long i = 0; i < rounds; i++)
    seed = seed * 6364136223846793005ULL + 1442695040888963407ULL;
  return seed;
}

static void report(const char *name, struct sysfs_summary s) {
  printf("%s count %llu min %llu median %llu p90 %llu max %llu mean %llu\n", name,
         (unsigned long long)s.count, (unsigned long long)s.min, (unsigned long long)s.median,
         (unsigned long long)s.p90, (unsigned long long)s.max, (unsigned long long)s.mean);
}

static struct sysfs_summary run(unsigned long rounds) {
  uint64_t sink = 0;
  for (int i = 0; i < SAMPLES; i++) {
    uint64_t before = sysfs_now_ns();
    sink += chew(i, rounds);
    uint64_t after = sysfs_now_ns();
    samples[i] = after - before;
  }
  if (sink == 0)
    printf("unreachable %llu\n", (unsigned long long)sink);
  return sysfs_summarise(samples, SAMPLES);
}

/* The bias experiment. `padding` bytes of stack are claimed and never read — the variable that
 * should not matter — which moves the buffer below it to a different address, and so into
 * different cache sets, on each run. The walk over that buffer is a dependent pointer chase, so
 * its time is decided by where the data landed and nothing else. The address the buffer reached is
 * reported with the timing, so that a run whose time did not move is a measurement of an
 * indifferent machine and not of a padding the compiler quietly removed. */
static struct sysfs_summary bias_run(unsigned long padding, uintptr_t *landed_at) {
  volatile char *claimed = alloca(padding ? padding : 1);
  for (unsigned long i = 0; i < (padding ? padding : 1); i++)
    claimed[i] = (char)i;

  size_t *ring = alloca(CHASE_SLOTS * sizeof(size_t));
  *landed_at = (uintptr_t)ring;
  for (size_t i = 0; i < CHASE_SLOTS; i++)
    ring[i] = 0;
  size_t at = 0;
  for (size_t k = 0; k < CHASE_SLOTS; k++) {
    size_t next = (at + CHASE_STRIDE) % CHASE_SLOTS;
    while (ring[next])
      next = (next + 1u) % CHASE_SLOTS;
    ring[at] = next;
    at = next;
  }

  size_t p = 0;
  for (int i = 0; i < SAMPLES; i++) {
    uint64_t before = sysfs_now_ns();
    for (int r = 0; r < CHASE_ROUNDS; r++)
      for (size_t j = 0; j < CHASE_SLOTS; j++)
        p = ring[p];
    uint64_t after = sysfs_now_ns();
    samples[i] = after - before;
  }
  if (p == 0xdeadbeef)
    printf("unreachable %zu\n", p);
  return sysfs_summarise(samples, SAMPLES);
}

int main(int argc, char **argv) {
  const char *what = argc > 1 ? argv[1] : "clock";

  printf("measuring 1\n");
  if (strcmp(what, "clock") == 0) {
    printf("clock cost_ns %llu\n", (unsigned long long)sysfs_clock_cost_ns());
    /* What the clock can resolve is not what it claims to report. A clock that returns
     * nanoseconds may still only ever change in steps, and the smallest non-zero difference
     * between two readings is the step. */
    uint64_t smallest = 0;
    for (int i = 0; i < SAMPLES; i++) {
      uint64_t before = sysfs_now_ns(), after;
      do {
        after = sysfs_now_ns();
      } while (after == before);
      uint64_t step = after - before;
      if (smallest == 0 || step < smallest)
        smallest = step;
    }
    printf("clock resolution_ns %llu\n", (unsigned long long)smallest);
  } else if (strcmp(what, "spread") == 0) {
    report("spread", run(WORK));
  } else if (strcmp(what, "bias") == 0) {
    /* Three runs of identical work, each with its data moved by a different, irrelevant amount of
     * claimed stack. Whether the time follows is the measurement, not an assumption. */
    static const unsigned long paddings[] = {0, 64, 512};
    for (size_t i = 0; i < sizeof paddings / sizeof paddings[0]; i++) {
      uintptr_t landed = 0;
      struct sysfs_summary s = bias_run(paddings[i], &landed);
      printf("bias_%lu count %llu min %llu median %llu p90 %llu max %llu mean %llu base %llu\n",
             paddings[i], (unsigned long long)s.count, (unsigned long long)s.min,
             (unsigned long long)s.median, (unsigned long long)s.p90, (unsigned long long)s.max,
             (unsigned long long)s.mean, (unsigned long long)(landed & 0xffffffULL));
    }
  } else {
    fprintf(stderr, "usage: measuring clock|spread|bias\n");
    return 2;
  }
  printf("end measuring\n");
  return 0;
}
