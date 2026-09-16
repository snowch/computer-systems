/* intrload — do a fixed amount of console and disk work, and say exactly how much.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The interrupts-and-drivers chapter counts interrupts by source. A count is only worth printing if the workload that caused it
 * is fixed by construction, so every quantity here is a constant this program decided and prints.
 *
 * Two devices, because they are interesting in different ways: the console is a character at a
 * time and the disk is a block at a time, and the ratio of interrupts to work differs by three
 * orders of magnitude between them.
 */

#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "user/user.h"

#define SYSFS_INTRLOAD_CHARS 512
#define SYSFS_INTRLOAD_BLOCKS 32
#define BLOCK 512

static char block[BLOCK];

int main(void) {
  /* Console: one write of a known number of characters, on one line so the transcript stays
   * readable. Every one of them has to reach a device that takes them one at a time. */
  static char line[SYSFS_INTRLOAD_CHARS + 1];
  for (int i = 0; i < SYSFS_INTRLOAD_CHARS; i++)
    line[i] = '.';
  write(1, line, SYSFS_INTRLOAD_CHARS);
  write(1, "\n", 1);

  /* Disk: a file written and read back, so the request count is decided here and not by a
   * cache's opinion of what is already in memory. */
  for (int i = 0; i < BLOCK; i++)
    block[i] = (char)i;

  int fd = open("intrload.dat", O_CREATE | O_WRONLY);
  for (int i = 0; i < SYSFS_INTRLOAD_BLOCKS; i++)
    write(fd, block, BLOCK);
  close(fd);

  fd = open("intrload.dat", O_RDONLY);
  for (int i = 0; i < SYSFS_INTRLOAD_BLOCKS; i++)
    read(fd, block, BLOCK);
  close(fd);
  unlink("intrload.dat");

  printf("intrload chars %d blocks %d\n", SYSFS_INTRLOAD_CHARS + 1, SYSFS_INTRLOAD_BLOCKS);
  printf("end intrload\n");
  exit(0);
}
