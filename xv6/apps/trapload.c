/* trapload, xv6 target: ask the kernel for exactly one thing, exactly this many times.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * ch08's census counts system calls by number. Counting the *shell* is no use as a measurement:
 * how many times it calls read depends on how the console delivered the characters, which
 * depends on timing, which inside QEMU is a property of the laptop. This program removes the
 * question. It calls getpid in a loop and nothing else calls getpid, so the census entry for it
 * is a number this program decided and the surrounding noise lands elsewhere.
 */

#include "kernel/types.h"
#include "user/user.h"

#define SYSFS_TRAPLOAD_CALLS 1000

int main(void) {
  int last = 0;
  for (int i = 0; i < SYSFS_TRAPLOAD_CALLS; i++) {
    last = getpid();
  }
  printf("trapload %d calls pid %d\n", SYSFS_TRAPLOAD_CALLS, last);
  exit(0);
}
