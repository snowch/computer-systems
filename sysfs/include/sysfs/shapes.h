/* Declarations for the functions the book disassembles.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Kept separate from probe.h because these are compiled for the host target only: they exist to
 * be read as machine code, and xv6's freestanding build has no reason to carry them.
 */

#ifndef SYSFS_SHAPES_H
#define SYSFS_SHAPES_H

int sysfs_clamp(int value, int low, int high);
long sysfs_sum(const int *values, unsigned long count);

#endif /* SYSFS_SHAPES_H */
