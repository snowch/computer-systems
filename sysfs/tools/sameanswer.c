/* sameanswer, host target: the same sum by two routes, and proof that they agree.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The xv6 build of this program is xv6/apps/sameanswer.c and differs only in which headers it
 * includes. That is the point of ch09's last section: identical arithmetic, identical output,
 * two machines.
 */

#include <stdio.h>

#include "sysfs/stages.h"

SYSFS_STAGES_DEFINE_SUMS

int main(void) {
  SYSFS_STAGES_REPORT(printf, "host");
  return 0;
}
