/* Small functions whose machine-level shape the book reads.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Each is chosen so that its disassembly says something. They are deliberately short enough to
 * hold in your head at once: the point is never the algorithm, it is what the compiler did with
 * it, and a function you have to scroll through teaches nothing about instruction selection.
 *
 * Compiled for both of the book's architectures and disassembled by bench/run_disasm.py, so the
 * listings in the chapters are generated from this file rather than pasted from a terminal on
 * somebody's laptop in 2026.
 */

#include "sysfs/shapes.h"

/* Two conditionals and three exits. The interesting question is whether the compiler emits
 * branches or conditional moves, and the two architectures answer it differently — which makes
 * this the smallest honest demonstration that instruction selection is not a detail. */
int sysfs_clamp(int value, int low, int high) {
  if (value < low) {
    return low;
  }
  if (value > high) {
    return high;
  }
  return value;
}

/* A loop with a carried dependency and a memory read per iteration. Later chapters use it to ask
 * what the load costs and whether the addition can overlap it; here it is just a second shape. */
long sysfs_sum(const int *values, unsigned long count) {
  long total = 0;
  for (unsigned long i = 0; i < count; i++) {
    total += values[i];
  }
  return total;
}
