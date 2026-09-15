/* layout — say where the fields are and whether they share a line.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * ch25's first measurement needs no machine: whether two counters land on the same cache line is
 * decided by the compiler and the layout, and both are knowable before anything runs. What that
 * costs needs four cores and is the rest of the chapter.
 */

#include <stddef.h>
#include <stdio.h>

#include "sysfs/sharing.h"

int main(void) {
  printf("layout 1\n");
  printf("line bytes %d\n", SYSFS_LINE_BYTES);
  printf("packed size %zu offsets %zu %zu same_line %d\n", sizeof(struct sysfs_packed),
         offsetof(struct sysfs_packed, a), offsetof(struct sysfs_packed, b),
         sysfs_same_line(offsetof(struct sysfs_packed, a), offsetof(struct sysfs_packed, b)));
  printf("padded size %zu offsets %zu %zu same_line %d\n", sizeof(struct sysfs_padded),
         offsetof(struct sysfs_padded, a), offsetof(struct sysfs_padded, b),
         sysfs_same_line(offsetof(struct sysfs_padded, a), offsetof(struct sysfs_padded, b)));
  printf("end layout\n");
  return 0;
}
