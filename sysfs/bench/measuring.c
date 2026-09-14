/* measuring — the three experiments chapter 14 is about, on the machine being measured.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   measuring clock        what reading the clock costs, and what it can resolve
 *   measuring spread       one fixed workload, many times, reported as a distribution
 *   measuring bias         the same workload made to give different answers by changing
 *                          something that should not matter
 *
 * Prints one fact per line, `kind name value`, like every other tool in this book. It takes no
 * decisions about what to report: that is the reader's job and the chapter's subject.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/timing.h"

#define SAMPLES 2000
#define WORK 20000

static uint64_t samples[SAMPLES];

/* The thing being measured: deliberately small, deliberately dependent, and deliberately
 * unoptimisable, so that the compiler cannot delete it and the machine cannot overlap it. */
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

static struct sysfs_summary run(unsigned long rounds, unsigned long padding) {
  /* `padding` is the thing that should not matter: bytes of stack claimed before the loop runs,
   * which changes nothing about the work and moves everything about where it lands in memory. */
  volatile char pad[4096];
  uint64_t sink = 0;

  memset((void *)pad, 0, padding < sizeof(pad) ? padding : sizeof(pad));
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
    report("spread", run(WORK, 0));
  } else if (strcmp(what, "bias") == 0) {
    /* Three runs of identical work, differing only in how much stack was claimed first. */
    report("bias_0", run(WORK, 0));
    report("bias_64", run(WORK, 64));
    report("bias_512", run(WORK, 512));
  } else {
    fprintf(stderr, "usage: measuring clock|spread|bias\n");
    return 2;
  }
  printf("end measuring\n");
  return 0;
}
