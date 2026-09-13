/* sysprobe, xv6 target: ask the teaching kernel the same questions the board gets asked.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Staged into the xv6 tree as user/sysprobe.c by scripts/xv6-prepare.py, which also copies
 * sysfs/include/sysfs/ to sysfs/ inside the staging tree — xv6 compiles with -I., so the include
 * below resolves there. See xv6/README.md.
 */

#include "kernel/types.h"
#include "user/user.h"

#include "sysfs/probe.h"

int main(void) {
  SYSFS_PROBE_ALL(printf, "xv6");
  exit(0);
}
