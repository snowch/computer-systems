/* sysprobe, host target: ask Linux on the board what its C implementation looks like.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The interesting file is sysfs/include/sysfs/probe.h. This one exists only to supply a printf
 * and a main, and its twin at xv6/apps/sysprobe.c does the same job for the other target. Their
 * output is expected to be identical, which is the first concrete thing the prerequisites chapter demonstrates:
 * the language and the ABI are the same on both targets, and everything the book says about time
 * is what differs.
 */

#include <stdio.h>

#include "sysfs/probe.h"

int main(void) {
  SYSFS_PROBE_ALL(printf, "host");
  return 0;
}
