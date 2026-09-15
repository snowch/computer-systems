/* Problems 12.1, 12.2 and 12.3 — account for the blocks, survive the crash, find the state.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository. The chapter's patch counts blocks and decides nothing.
 *
 *   python3 -m pytest tests/the_file_system
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 12.1 -------------------------------------------------------------------------- */
/* How many blocks reach the disk for a transaction that modifies `blocks` distinct blocks?
 *
 * This file system writes a transaction twice: once into the log, and once to the blocks' real
 * homes. Around that it writes the log's header — once to say what the transaction contains, and
 * once to say that it no longer does.
 *
 * Return the total number of block writes, or 0 for a transaction that modifies nothing, which is
 * never committed at all.
 *
 * Modifying the same block twice inside one transaction is still one block: the log holds blocks,
 * not changes, and `blocks` is already the count of distinct ones.
 */
uint64_t fs_writes_for(uint64_t blocks) {
  (void)blocks;
  return 0; /* Problem 12.1 */
}

/* -- Problem 12.2 -------------------------------------------------------------------------- */
/* What does the file system find after a crash at this point?
 *
 * A transaction goes through four stages in order:
 *
 *   0  nothing written yet
 *   1  the blocks are in the log, and the header does not mention them
 *   2  the header has been written, naming the blocks: the transaction is committed
 *   3  the blocks have been copied to their homes
 *   4  the header has been cleared
 *
 * Return what recovery must do if the power fails after the given stage:
 *
 *   FS_NOTHING  the transaction never happened, and there is nothing to undo
 *   FS_REPLAY   the transaction did happen, and the blocks must be copied to their homes
 *
 * The whole design is in one place. Writing the header is the single instant at which the
 * transaction becomes real: before it, blocks sitting in the log are ignorable; after it, they
 * are authoritative. There is no stage at which half a transaction is visible, and arranging that
 * is the only thing the log is for.
 */
#define FS_NOTHING 0
#define FS_REPLAY 1

int fs_after_crash(int stage) {
  (void)stage;
  return FS_NOTHING; /* Problem 12.2 */
}

/* -- Problem 12.3 -------------------------------------------------------------------------- */
/* Is this ordering safe?
 *
 * `order` is the order in which three things are written: 'l' for the log blocks, 'h' for the log
 * header naming them, and 'b' for the blocks at their real homes. Return 1 if a crash at every
 * point in that ordering leaves the file system consistent, and 0 if there is a point at which it
 * does not.
 *
 * Do not reason about which crash is likely. A design is safe when every prefix of what it writes
 * is survivable, and unsafe when one of them is not — and the unsafe orderings here are the ones
 * that look reasonable.
 */
int fs_ordering_safe(const char *order) {
  (void)order;
  return 1; /* Problem 12.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    switch (argv[i][0]) {
    case 'w': /* w<blocks> */
      printf("writes %s %llu\n", argv[i] + 1,
             (unsigned long long)fs_writes_for(strtoull(argv[i] + 1, NULL, 0)));
      break;
    case 'c': /* c<stage> */
      printf("crash %s %d\n", argv[i] + 1, fs_after_crash(atoi(argv[i] + 1)));
      break;
    case 'o': /* o<order> */
      printf("safe %s %d\n", argv[i] + 1, fs_ordering_safe(argv[i] + 1));
      break;
    default:
      fprintf(stderr, "filesystem: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end filesystem\n");
  return 0;
}
