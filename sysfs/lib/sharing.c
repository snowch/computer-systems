/* See sysfs/include/sysfs/sharing.h.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/sharing.h"

int sysfs_same_line(uint64_t first, uint64_t second) {
  return (first / SYSFS_LINE_BYTES) == (second / SYSFS_LINE_BYTES);
}
