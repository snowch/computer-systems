/* Four pairs of functions that a reader would call identical, and a compiler does not.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The representing-information chapter reads the disassembly of these rather than describing them. Each pair differs by one
 * word — `int` against `unsigned` — and the machine code differs by far more than that, because
 * the two types do not make the same promises and the compiler is allowed to use the difference.
 */

#ifndef SYSFS_SIGNEDNESS_H
#define SYSFS_SIGNEDNESS_H

/* Does adding one to this make it bigger? The two answers are not the same answer. */
int sysfs_signed_grows(int x);
int sysfs_unsigned_grows(unsigned x);

/* A quarter of it, rounded the way C says to round. */
int sysfs_signed_quarter(int x);
unsigned sysfs_unsigned_quarter(unsigned x);

#endif /* SYSFS_SIGNEDNESS_H */
