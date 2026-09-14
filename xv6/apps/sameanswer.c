/* sameanswer, xv6 target: the same sum by two routes, on the teaching kernel.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Staged into the xv6 tree as user/sameanswer.c by the staging step, which also copies
 * sysfs/include/sysfs/ to sysfs/ inside the stage. See xv6/README.md.
 */

#include "kernel/types.h"
#include "user/user.h"

#include "sysfs/stages.h"

SYSFS_STAGES_DEFINE_SUMS

int main(void) {
  SYSFS_STAGES_REPORT(printf, "xv6");
  exit(0);
}
