/* switchload — make a fixed number of processes come and go, and say how many.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The scheduling chapter counts context switches by why the process gave up the CPU. Only one of those reasons is
 * a number a workload can fix: a process that exits switches away exactly once and does not come
 * back. How many times the timer took the CPU away, and how many times a process waited for
 * something that had not happened yet, are facts about how long things took.
 */

#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

#define SYSFS_SWITCHLOAD_CHILDREN 16

int main(void) {
  for (int i = 0; i < SYSFS_SWITCHLOAD_CHILDREN; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("switchload fork failed\n");
      exit(1);
    }
    if (pid == 0)
      exit(0); /* the whole of the child: be born, and stop */
    wait(0);
  }
  printf("switchload children %d\n", SYSFS_SWITCHLOAD_CHILDREN);
  printf("end switchload\n");
  exit(0);
}
