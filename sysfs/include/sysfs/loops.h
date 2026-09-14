/* Five ways to write the same loop, for the chapter about what the compiler already does.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Every one of these computes the same result from the same input. They differ in which
 * hand-optimisation has been applied — hoisting, unrolling, strength reduction, and the
 * combination — and ch16's question is which of those the compiler was going to do anyway.
 *
 * The answer is not obvious in advance and is not the same at every optimisation level, which is
 * the reason the chapter measures rather than asserting.
 */

#ifndef SYSFS_LOOPS_H
#define SYSFS_LOOPS_H

/* The obvious version: a bound recomputed each time, a multiply in the body, nothing helped. */
long sysfs_loop_plain(const long *values, long count, long scale);

/* The bound hoisted into a local, which is the transformation people reach for first. */
long sysfs_loop_hoisted(const long *values, long count, long scale);

/* The multiply replaced by repeated addition: strength reduction, done by hand. */
long sysfs_loop_reduced(const long *values, long count, long scale);

/* Four iterations per pass, with the remainder handled separately. */
long sysfs_loop_unrolled(const long *values, long count, long scale);

/* All three at once, which is either the fastest or exactly the same. */
long sysfs_loop_everything(const long *values, long count, long scale);

#endif /* SYSFS_LOOPS_H */
