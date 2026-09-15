/* Problems 18.1, 18.2 and 18.3 — find the sharing, predict the curve, translate the fence.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository. `sysfs/lib/sharing.c` answers whether two offsets share a
 * line and nothing else.
 *
 *   python3 -m pytest tests/ch25
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LINE 64

/* -- Problem 18.1 -------------------------------------------------------------------------- */
/* Which fields will two cores fight over?
 *
 * `offsets` holds the byte offset of each of `count` fields within one structure, and `written_by`
 * says which thread writes each — a small integer, or -1 for a field nobody writes.
 *
 * Return the number of *pairs* of fields that are written by different threads and land on the
 * same cache line. Those are the pairs that cause false sharing; every other pair costs nothing,
 * including two fields on one line written by the same thread.
 *
 * The distinction is the whole problem. Sharing a line is not the fault; sharing a line with
 * somebody else's writes is.
 */
uint64_t s_contended_pairs(const uint64_t *offsets, const int *written_by, uint64_t count) {
  (void)offsets;
  (void)written_by;
  (void)count;
  return 0; /* Problem 18.1 */
}

/* -- Problem 18.2 -------------------------------------------------------------------------- */
/* What does the scaling curve look like?
 *
 * A workload takes `total` units of work and splits it evenly across `threads` cores. A fraction
 * of the work, `serial_percent`, cannot be parallelised at all.
 *
 * Return the speedup over one thread, times 100 and rounded down, as Amdahl's law gives it:
 * the serial part takes as long as it ever did and the rest divides.
 *
 * Do this before measuring anything. A predicted curve you then fail to reach tells you there is
 * something to find; a measured curve with nothing to compare it against tells you very little.
 */
uint64_t s_speedup_x100(uint64_t total, uint64_t threads, uint64_t serial_percent) {
  (void)total;
  (void)threads;
  (void)serial_percent;
  return 100; /* Problem 18.2 */
}

/* -- Problem 18.3 -------------------------------------------------------------------------- */
/* Same requirement, two architectures.
 *
 * `need` is what the program requires: 'r' for release (earlier work must not move after this
 * store), 'a' for acquire (later work must not move before this load), 'f' for a full fence.
 * `isa` is 'r' for RISC-V or 'a' for AArch64.
 *
 * Write into `spelling` the mnemonic this book's chapters saw the compiler emit, and return 1; or
 * return 0 if `need` is not one of the three.
 *
 *   RISC-V:   release -> "fence rw,w"   acquire -> "fence r,rw"   full -> "fence rw,rw"
 *   AArch64:  release -> "stlr"          acquire -> "ldar"         full -> "dmb ish"
 *
 * The point is not the table. It is that the left column is the requirement, the right two are
 * spellings of it, and a reader who learned one and thinks it is the concept will not recognise
 * the other as a barrier at all — AArch64's release is not an instruction *between* two others,
 * it is a property of one of them.
 */
int s_spelling(char need, char isa, char *spelling) {
  (void)need;
  (void)isa;
  (void)spelling;
  return 0; /* Problem 18.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

#define MAX_FIELDS 64

int main(int argc, char **argv) {
  uint64_t offsets[MAX_FIELDS];
  int owners[MAX_FIELDS];
  char spelling[32];

  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    switch (argv[i][0]) {
    case 'p': { /* p<index>,<offset>:<owner>.<offset>:<owner>... */
      if (comma == NULL)
        return 2;
      *comma = '\0';
      uint64_t n = 0;
      for (char *p = comma + 1; *p && n < MAX_FIELDS;) {
        offsets[n] = strtoull(p, &p, 10);
        if (*p == ':')
          p++;
        owners[n] = (int)strtol(p, &p, 10);
        n++;
        if (*p == '.')
          p++;
      }
      printf("pairs %s %llu\n", argv[i] + 1,
             (unsigned long long)s_contended_pairs(offsets, owners, n));
      break;
    }
    case 's': { /* s<total>,<threads>,<serial> */
      if (comma == NULL)
        return 2;
      char *second = strchr(comma + 1, ',');
      if (second == NULL)
        return 2;
      printf("speedup %s %llu\n", argv[i] + 1,
             (unsigned long long)s_speedup_x100(strtoull(argv[i] + 1, NULL, 10),
                                                strtoull(comma + 1, NULL, 10),
                                                strtoull(second + 1, NULL, 10)));
      break;
    }
    case 'f': /* f<need><isa> */
      memset(spelling, 0, sizeof(spelling));
      if (s_spelling(argv[i][1], argv[i][2], spelling))
        printf("spelling %c%c %s\n", argv[i][1], argv[i][2], spelling);
      else
        printf("spelling %c%c -\n", argv[i][1], argv[i][2]);
      break;
    default:
      fprintf(stderr, "sharing: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end sharing\n");
  return 0;
}
