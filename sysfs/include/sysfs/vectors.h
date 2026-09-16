/* Five loops, three of which the compiler will widen and two of which it will not.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The vectors chapter asks one question: what does vectorising buy, and when will the compiler do it
 * without being asked? These loops exist to make both halves of that answerable by looking —
 * `bench/run_vectors.py` counts how many of each function's instructions are vector instructions,
 * which is a property of the compiler and needs no machine.
 *
 * Nothing here is written in intrinsics. A chapter about what the compiler will do on its own
 * cannot be written in a notation that takes the decision away from it.
 */

#ifndef SYSFS_VECTORS_H
#define SYSFS_VECTORS_H

#include <stdint.h>

/* The easy one: independent elements, one multiply each, no reduction, no indirection. If a
 * compiler will not widen this, it will not widen anything. */
void sysfs_vec_scale(float *out, const float *in, float k, uint64_t n);

/* A reduction over integers. Every partial sum can be computed in any order and the answer is the
 * same, because integer addition is associative — which is a fact about arithmetic and not about
 * the compiler, and it is the whole reason this one widens and the next does not. */
int64_t sysfs_vec_sum_i32(const int32_t *x, uint64_t n);

/* The same reduction over floats. Floating-point addition is *not* associative: adding the same
 * numbers in a different order can give a different answer. Widening this loop means adding them
 * in a different order, so a compiler that did it without being asked would be changing the
 * program's output — and it will not. */
float sysfs_vec_sum_f32(const float *x, uint64_t n);

/* An indirection. The elements are independent, but their addresses are not known until the
 * indices are loaded, so the data has to be gathered rather than read in a run. */
void sysfs_vec_gather(float *out, const float *in, const int32_t *index, uint64_t n);

/* A loop-carried dependence: each element needs the one before it. No amount of width helps,
 * because the second lane cannot start until the first has finished. */
void sysfs_vec_running(float *out, const float *in, uint64_t n);

#endif /* SYSFS_VECTORS_H */
