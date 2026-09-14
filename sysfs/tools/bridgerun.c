/* bridgerun — the host-target half of ch13's crossing.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The same source as the xv6 half, compiled for the other architecture. It prints what the two
 * routes computed and whether they agree, and it prints no duration: a host-target binary is run
 * under user-mode QEMU in CI to check its answers, and answers are all that means anything there.
 * The timing belongs to `make bench-board` and to nowhere else.
 */

#include <stdio.h>
#include <stdlib.h>

#include "sysfs/bridge.h"

SYSFS_BRIDGE_DEFINE

#define SYSFS_BRIDGE_CELLS 4096

static struct sysfs_cell cells[SYSFS_BRIDGE_CELLS];

int main(void) {
  long stride = sysfs_bridge_stride(SYSFS_BRIDGE_CELLS);

  sysfs_bridge_fill(cells, SYSFS_BRIDGE_CELLS, stride);
  long sequential = sysfs_bridge_sequential(cells, SYSFS_BRIDGE_CELLS);
  long chased = sysfs_bridge_chased(cells, SYSFS_BRIDGE_CELLS);

  printf("bridge cells %d stride %ld\n", SYSFS_BRIDGE_CELLS, stride);
  printf("bridge sequential %ld chased %ld agree %s\n", sequential, chased,
         sequential == chased ? "yes" : "no");
  printf("end bridge\n");
  return 0;
}
