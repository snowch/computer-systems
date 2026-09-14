/* bridgerun — run both halves of ch13's program on the xv6 target and report what they computed.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * What is reported is the *answer*, not a duration. This target cannot be asked what anything
 * costs, and ch13 is the chapter that says so at length before doing it anyway on hardware.
 */

#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "sysfs/bridge.h"

SYSFS_BRIDGE_DEFINE

#define SYSFS_BRIDGE_CELLS 4096

static struct sysfs_cell cells[SYSFS_BRIDGE_CELLS];

int main(void) {
  long stride = sysfs_bridge_stride(SYSFS_BRIDGE_CELLS);

  sysfs_bridge_fill(cells, SYSFS_BRIDGE_CELLS, stride);
  long sequential = sysfs_bridge_sequential(cells, SYSFS_BRIDGE_CELLS);
  long chased = sysfs_bridge_chased(cells, SYSFS_BRIDGE_CELLS);

  printf("bridge cells %d stride %d\n", SYSFS_BRIDGE_CELLS, (int)stride);
  printf("bridge sequential %d chased %d agree %s\n", (int)sequential, (int)chased,
         sequential == chased ? "yes" : "no");
  printf("end bridge\n");
  exit(0);
}
