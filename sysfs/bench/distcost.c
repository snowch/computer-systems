/* The measurement chapter's workload: one small loop, timed honestly, twice.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The work itself is deliberately dull — sum an array small enough to sit in the first-level
 * cache — because the chapter is about the instrument rather than about the workload. Anything
 * with interesting memory behaviour would put the memory chapter's subject inside the
 * measurement chapter's experiment, and then a spread would have two explanations.
 *
 * Two variants, differing only in unroll factor, because "is B faster than A" needs a B that
 * might plausibly be faster and might plausibly be neither.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "sysfs/distribution.h"
#include "sysfs/timing.h"

/* 4096 uint32_t is 16 KiB: comfortably inside a 64 KiB first-level data cache, so every run
 * after the first reads from it and the memory hierarchy is not part of what is being timed. */
#define ELEMENTS 4096u
#define ROUNDS 64u

struct workload {
  uint32_t *data;
  uint64_t sink;
};

/* The plain version: one element per iteration, nothing clever. */
static void sum_plain(void *context) {
  struct workload *w = context;
  uint64_t total = 0;
  for (unsigned r = 0; r < ROUNDS; r++)
    for (unsigned i = 0; i < ELEMENTS; i++)
      total += w->data[i];
  w->sink += total;
}

/* Four per iteration. Whether this is faster is the question, not the claim. */
static void sum_unrolled(void *context) {
  struct workload *w = context;
  uint64_t a = 0, b = 0, c = 0, d = 0;
  for (unsigned r = 0; r < ROUNDS; r++)
    for (unsigned i = 0; i < ELEMENTS; i += 4) {
      a += w->data[i];
      b += w->data[i + 1];
      c += w->data[i + 2];
      d += w->data[i + 3];
    }
  w->sink += a + b + c + d;
}

/* An empty measured region, for measuring the harness itself.
 *
 * It is not empty to the compiler — the sink is volatile-adjacent through the struct — but it
 * does none of the work above, so what it times is the clock, the call and the loop around them.
 */
static void sum_nothing(void *context) {
  struct workload *w = context;
  w->sink += 1;
}

int main(int argc, char **argv) {
  struct sysfs_run_spec spec;
  if (sysfs_parse_run_spec(argc, argv, &spec) != 0)
    return 2;

  const char *which = "plain";
  for (int i = 1; i + 1 < argc; i += 2)
    if (argv[i][0] == '-' && argv[i][1] == '-' && argv[i][2] == 'w')
      which = argv[i + 1];

  struct workload work = {.data = malloc(ELEMENTS * sizeof *work.data), .sink = 0};
  if (!work.data)
    return 1;
  for (unsigned i = 0; i < ELEMENTS; i++)
    work.data[i] = i * 2654435761u;

  void (*body)(void *) = sum_plain;
  if (which[0] == 'u')
    body = sum_unrolled;
  else if (which[0] == 'n')
    body = sum_nothing;

  int failed = sysfs_run_distribution(&spec, body, &work);

  /* The sum is printed so nothing above can be optimised away, and so a run that computed the
   * wrong thing is visible rather than merely fast. */
  printf("distcost variant %s sink %llu runs %llu warmup %llu mode %s\n", which,
         (unsigned long long)work.sink, (unsigned long long)spec.runs,
         (unsigned long long)spec.warmup_runs, spec.cold ? "cold" : "warm");
  free(work.data);
  return failed;
}
