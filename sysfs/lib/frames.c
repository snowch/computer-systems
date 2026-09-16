/* The functions the RISC-V machine-code chapter measures the frames of.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/frames.h"

int sysfs_leaf(int a, int b) { return a * b + a; }

/* Deliberately not static and not defined here: the compiler must assume the worst about it,
 * which is what makes the callers below into real non-leaf functions. */
extern int sysfs_opaque(int value);

int sysfs_calls_out(int value) { return sysfs_opaque(value) + 1; }

long sysfs_many_locals(long a, long b, long c, long d, long e, long f, long g, long h) {
  long p = a * b;
  long q = c * d;
  long r = e * f;
  long s = g * h;
  /* Every intermediate is still needed after the next one is computed, so they cannot share a
   * register — which is how a function comes to have more live values than the machine has
   * places to put them. */
  return (p + q) * (r + s) + (p - s) * (q - r);
}

long sysfs_accumulates(const long *values, unsigned long count) {
  long total = 0;
  for (unsigned long index = 0; index < count; index++) {
    total += sysfs_opaque((int)values[index]);
  }
  return total;
}
