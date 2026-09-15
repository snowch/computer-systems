/* The C that appendix G has to justify rather than assert.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * A syntax reference is the most-copied artefact in computing, and a copied one would be worth
 * nothing here. These functions exist so that the two claims most likely to be taken on trust —
 * that `p + 1` advances by the size of what `p` points at, and that `->` is not an operation the
 * machine has heard of — are settled by disassembly instead.
 */

#ifndef SYSFS_DECLARATIONS_H
#define SYSFS_DECLARATIONS_H

#include <stdint.h>

/* Two pointers, the same `+ 1`, element types of different widths. The instruction that computes
 * each address says how far one step is, which is the fact that makes pointer arithmetic
 * readable — and it is not visible in the source at all. */
int32_t sysfs_step_narrow(const int32_t *p);
int64_t sysfs_step_wide(const int64_t *p);

/* A struct reached through a pointer. `->` compiles to an offset on a load: there is no member
 * lookup at run time, and the name is gone by the time the machine sees it. */
struct sysfs_record {
  int32_t first;
  int32_t second;
  int64_t third;
};

int64_t sysfs_reach_through(const struct sysfs_record *record);

#endif /* SYSFS_DECLARATIONS_H */
