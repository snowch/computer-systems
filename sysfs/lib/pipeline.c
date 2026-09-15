/* See sysfs/include/sysfs/pipeline.h.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/pipeline.h"

long sysfs_sum_chain1(const long *values, long count) {
  long a = 0;

  for (long i = 0; i < count; i++)
    a += values[i];
  return a;
}

long sysfs_sum_chain2(const long *values, long count) {
  long a = 0, b = 0;
  long i = 0;

  for (; i + 1 < count; i += 2) {
    a += values[i];
    b += values[i + 1];
  }
  for (; i < count; i++)
    a += values[i];
  return a + b;
}

long sysfs_sum_chain4(const long *values, long count) {
  long a = 0, b = 0, c = 0, d = 0;
  long i = 0;

  for (; i + 3 < count; i += 4) {
    a += values[i];
    b += values[i + 1];
    c += values[i + 2];
    d += values[i + 3];
  }
  for (; i < count; i++)
    a += values[i];
  return a + b + c + d;
}

long sysfs_sum_chain8(const long *values, long count) {
  long a = 0, b = 0, c = 0, d = 0, e = 0, f = 0, g = 0, h = 0;
  long i = 0;

  for (; i + 7 < count; i += 8) {
    a += values[i];
    b += values[i + 1];
    c += values[i + 2];
    d += values[i + 3];
    e += values[i + 4];
    f += values[i + 5];
    g += values[i + 6];
    h += values[i + 7];
  }
  for (; i < count; i++)
    a += values[i];
  return a + b + c + d + e + f + g + h;
}

long sysfs_count_over(const long *values, long count, long threshold) {
  long hits = 0;

  /* Deliberately a branch rather than arithmetic. A compiler that turns this into a conditional
   * move removes the thing being measured, and ch19 says how to notice that it has. */
  for (long i = 0; i < count; i++)
    if (values[i] > threshold)
      hits++;
  return hits;
}


/* Deliberately not inlinable and deliberately not visible: the compiler must assume the call
 * could do anything, which is what stops it flattening the branch that reaches it. */
__attribute__((noinline)) static long tick(long hits) { return hits + 1; }

long sysfs_count_over_calling(const long *values, long count, long threshold) {
  long hits = 0;

  for (long i = 0; i < count; i++)
    if (values[i] > threshold)
      hits = tick(hits);
  return hits;
}
