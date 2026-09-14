/* sv39 — do RISC-V address translation's arithmetic by hand, on any machine.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   sv39 decode 0x3fffffe000
 *   sv39 tables 0x0:4 0x3fffffe000:2
 *
 * ch07's claim is that a page table's size is decided by *where* an address space's pages are and
 * not by how many of them there are. `tables` is that claim as a function: hand it the runs of
 * pages an address space maps and it says how many page-table pages Sv39 needs to describe them,
 * without looking at a machine. The chapter checks its answer against a running kernel's count of
 * its own tables — which is a stronger thing than either number alone, because the two were
 * arrived at from opposite ends.
 *
 * Prints one fact per line, `kind name value...`, like every other tool in this book.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/sv39.h"

#define MAX_RUNS 512

static void constants(void) {
  printf("constant page_bytes %u\n", SYSFS_SV39_PAGE_BYTES);
  printf("constant entry_bytes %u\n", SYSFS_SV39_ENTRY_BYTES);
  printf("constant entries_per_table %u\n", SYSFS_SV39_ENTRIES);
  printf("constant index_bits %u\n", SYSFS_SV39_INDEX_BITS);
  printf("constant levels %u\n", SYSFS_SV39_LEVELS);
  for (int level = SYSFS_SV39_LEVELS - 1; level >= 0; level--)
    printf("span %d %llu\n", level, (unsigned long long)sysfs_sv39_span(level));
}

static int decode(const char *text) {
  uint64_t va = strtoull(text, NULL, 0);
  printf("decode %s l2 %u l1 %u l0 %u offset %u canonical %d\n", text, sysfs_sv39_index(va, 2),
         sysfs_sv39_index(va, 1), sysfs_sv39_index(va, 0), sysfs_sv39_offset(va),
         sysfs_sv39_canonical(va));
  /* Reassembling it is the check that the split lost nothing, and costs one line. */
  uint64_t back = sysfs_sv39_compose(sysfs_sv39_index(va, 2), sysfs_sv39_index(va, 1),
                                     sysfs_sv39_index(va, 0), sysfs_sv39_offset(va));
  printf("recompose %s %s\n", text, back == va ? "yes" : "no");
  return 0;
}

static int tables(int count, char **args) {
  struct sysfs_sv39_run runs[MAX_RUNS];
  uint64_t out[3];

  if (count > MAX_RUNS) {
    fprintf(stderr, "sv39: %d runs is more than this tool carries (%d)\n", count, MAX_RUNS);
    return 1;
  }
  for (int i = 0; i < count; i++) {
    char *colon = strchr(args[i], ':');
    if (colon == NULL) {
      fprintf(stderr, "sv39: expected start:pages, got %s\n", args[i]);
      return 1;
    }
    runs[i].start = strtoull(args[i], NULL, 0);
    runs[i].pages = strtoull(colon + 1, NULL, 0);
    if (i > 0 && runs[i].start < runs[i - 1].start) {
      fprintf(stderr, "sv39: runs must be sorted; %s follows %s\n", args[i], args[i - 1]);
      return 1;
    }
  }

  uint64_t total = sysfs_sv39_tables(runs, (size_t)count, out);
  printf("tables l2 %llu l1 %llu l0 %llu total %llu\n", (unsigned long long)out[2],
         (unsigned long long)out[1], (unsigned long long)out[0], (unsigned long long)total);
  return 0;
}

int main(int argc, char **argv) {
  int status;

  if (argc < 2) {
    fprintf(stderr, "usage: sv39 decode <address> | sv39 tables <start:pages>...\n");
    return 2;
  }

  printf("sv39 1\n");
  constants();
  if (strcmp(argv[1], "decode") == 0 && argc == 3)
    status = decode(argv[2]);
  else if (strcmp(argv[1], "tables") == 0 && argc > 2)
    status = tables(argc - 2, argv + 2);
  else {
    fprintf(stderr, "usage: sv39 decode <address> | sv39 tables <start:pages>...\n");
    return 2;
  }
  printf("end sv39\n");
  return status;
}
