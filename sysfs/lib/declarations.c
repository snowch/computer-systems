/* Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE. */

#include "sysfs/declarations.h"

int32_t sysfs_step_narrow(const int32_t *p) { return *(p + 1); }

int64_t sysfs_step_wide(const int64_t *p) { return *(p + 1); }

int64_t sysfs_reach_through(const struct sysfs_record *record) {
  return record->third + record->second;
}
