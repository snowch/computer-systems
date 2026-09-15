/* Problem 16.3 — which of these benchmark loops does the compiler delete?
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Every function below does the same arithmetic in a loop. They differ only in what becomes of
 * the result, and that is the whole question: a compiler may remove work whose result nothing can
 * observe, and a benchmark whose work has been removed reports a spectacular and entirely false
 * speedup.
 *
 * You are not editing this file. You are predicting, in problem_3_escapes.py, which of these the
 * compiler keeps — and the test finds out by compiling them and counting.
 */

#include <stdio.h>
#include <stdint.h>

#define ROUNDS 1000

/* The arithmetic, identical in every case below. */
#define SYSFS_ESCAPES_WORK(acc)                       \
  for (int i = 0; i < ROUNDS; i++)                    \
    (acc) = (acc) * 6364136223846793005ULL + 1442695040888963407ULL;

/* a — the result is computed into a local and then dropped on the floor. */
void escapes_dropped(uint64_t seed) {
  uint64_t acc = seed;
  SYSFS_ESCAPES_WORK(acc)
}

/* b — the result is returned. */
uint64_t escapes_returned(uint64_t seed) {
  uint64_t acc = seed;
  SYSFS_ESCAPES_WORK(acc)
  return acc;
}

/* c — the result is stored through a volatile, which the compiler may not elide. */
static volatile uint64_t escapes_sink;
void escapes_volatile(uint64_t seed) {
  uint64_t acc = seed;
  SYSFS_ESCAPES_WORK(acc)
  escapes_sink = acc;
}

/* d — the result is stored to a plain file-scope variable nothing ever reads. */
static uint64_t escapes_quiet;
void escapes_stored(uint64_t seed) {
  uint64_t acc = seed;
  SYSFS_ESCAPES_WORK(acc)
  escapes_quiet = acc;
}

/* e — the result decides whether something is printed, but the condition is never true. */
void escapes_conditional(uint64_t seed) {
  uint64_t acc = seed;
  SYSFS_ESCAPES_WORK(acc)
  if (acc == 1)
    printf("unreachable\n");
}
