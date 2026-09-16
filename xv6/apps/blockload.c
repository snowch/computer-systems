/* blockload — do the same file operations twice, once with a one-byte write and once without.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The file-system chapter's measurement is an amplification factor, and the honest version of it is a difference.
 * Running this program costs the file system something before `main` starts: the shell forks, the
 * kernel reads the binary, the directory is consulted. Measuring one run would charge all of that
 * to the byte.
 *
 * So the same program does the same work twice, differing in one `write` call, and the chapter
 * subtracts. Everything that is not the byte appears in both and cancels.
 *
 *   blockload quiet   create the file, close it, remove it
 *   blockload byte    create the file, write one byte, close it, remove it
 */

#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/fcntl.h"
#include "user/user.h"

#define SYSFS_BLOCKLOAD_BYTES 1

int main(int argc, char *argv[]) {
  int write_it = argc > 1 && argv[1][0] == 'b';
  char byte = 'x';

  int fd = open("blockload.dat", O_CREATE | O_WRONLY);
  if (fd < 0) {
    printf("blockload open failed\n");
    exit(1);
  }
  if (write_it && write(fd, &byte, SYSFS_BLOCKLOAD_BYTES) != SYSFS_BLOCKLOAD_BYTES) {
    printf("blockload write failed\n");
    exit(1);
  }
  close(fd);
  unlink("blockload.dat");

  printf("blockload wrote %d\n", write_it ? SYSFS_BLOCKLOAD_BYTES : 0);
  printf("end blockload\n");
  exit(0);
}
