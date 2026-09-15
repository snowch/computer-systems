/* See sysfs/include/sysfs/loops.h.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Written to be compiled and compared rather than to be admired. The hand-optimised versions are
 * what a careful programmer writes when they do not trust the compiler, which is the habit ch23
 * is about examining.
 */

#include "sysfs/loops.h"

/* A function the compiler cannot see the body of would defeat every transformation below, which
 * is a different chapter's subject. Here everything is visible, deliberately. */
static long weight(long index, long scale) { return index * scale; }

long sysfs_loop_plain(const long *values, long count, long scale) {
  long total = 0;

  for (long i = 0; i < count; i++)
    total += values[i] * weight(i, scale);
  return total;
}

long sysfs_loop_hoisted(const long *values, long count, long scale) {
  long total = 0;
  const long limit = count;

  for (long i = 0; i < limit; i++)
    total += values[i] * (i * scale);
  return total;
}

long sysfs_loop_reduced(const long *values, long count, long scale) {
  long total = 0;
  long running = 0; /* i * scale, maintained by addition rather than recomputed */

  for (long i = 0; i < count; i++) {
    total += values[i] * running;
    running += scale;
  }
  return total;
}

long sysfs_loop_unrolled(const long *values, long count, long scale) {
  long total = 0;
  long i = 0;

  for (; i + 3 < count; i += 4) {
    total += values[i] * (i * scale);
    total += values[i + 1] * ((i + 1) * scale);
    total += values[i + 2] * ((i + 2) * scale);
    total += values[i + 3] * ((i + 3) * scale);
  }
  for (; i < count; i++)
    total += values[i] * (i * scale);
  return total;
}

long sysfs_loop_everything(const long *values, long count, long scale) {
  long total = 0;
  long running = 0;
  long i = 0;
  const long limit = count;

  for (; i + 3 < limit; i += 4) {
    total += values[i] * running;
    running += scale;
    total += values[i + 1] * running;
    running += scale;
    total += values[i + 2] * running;
    running += scale;
    total += values[i + 3] * running;
    running += scale;
  }
  for (; i < limit; i++) {
    total += values[i] * running;
    running += scale;
  }
  return total;
}
