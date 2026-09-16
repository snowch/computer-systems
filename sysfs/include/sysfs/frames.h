/* Four functions chosen so that their stack frames are different from each other.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The RISC-V machine-code chapter compiles these at -O0 and at -O2 and compares what the compiler did about the stack. A
 * leaf function may need no frame at all; one that calls something must keep a return address
 * somewhere; one with more live values than there are registers has to put the rest in memory.
 * The point is that "how big is a stack frame" has no general answer, only a measured one.
 */

#ifndef SYSFS_FRAMES_H
#define SYSFS_FRAMES_H

/* Calls nothing. A leaf. */
int sysfs_leaf(int a, int b);

/* Calls something, so the return address in `ra` is no longer safe where it is. */
int sysfs_calls_out(int value);

/* More live values than the argument registers can carry. */
long sysfs_many_locals(long a, long b, long c, long d, long e, long f, long g, long h);

/* A loop with a call inside it: the value being accumulated has to survive each call. */
long sysfs_accumulates(const long *values, unsigned long count);

#endif /* SYSFS_FRAMES_H */
