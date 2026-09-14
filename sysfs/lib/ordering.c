/* See sysfs/include/sysfs/ordering.h.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/ordering.h"

void sysfs_bump_plain(long *counter) { (*counter)++; }

void sysfs_bump_relaxed(long *counter) { __atomic_fetch_add(counter, 1, __ATOMIC_RELAXED); }

void sysfs_bump_ordered(long *counter) { __atomic_fetch_add(counter, 1, __ATOMIC_SEQ_CST); }

void sysfs_publish(long *value, int *flag, long payload) {
  __atomic_store_n(value, payload, __ATOMIC_RELAXED);
  __atomic_store_n(flag, 1, __ATOMIC_RELEASE);
}

void sysfs_publish_unordered(long *value, int *flag, long payload) {
  *value = payload;
  *flag = 1;
}
