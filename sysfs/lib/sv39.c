/* Sv39 arithmetic. See sysfs/include/sysfs/sv39.h.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/sv39.h"

#define INDEX_MASK ((1u << SYSFS_SV39_INDEX_BITS) - 1)
#define OFFSET_MASK ((1u << SYSFS_SV39_PAGE_SHIFT) - 1)

static int shift_for(int level) {
  return SYSFS_SV39_PAGE_SHIFT + SYSFS_SV39_INDEX_BITS * level;
}

unsigned sysfs_sv39_index(uint64_t va, int level) {
  return (unsigned)((va >> shift_for(level)) & INDEX_MASK);
}

unsigned sysfs_sv39_offset(uint64_t va) {
  return (unsigned)(va & OFFSET_MASK);
}

uint64_t sysfs_sv39_span(int level) {
  return (uint64_t)1 << shift_for(level);
}

uint64_t sysfs_sv39_compose(unsigned l2, unsigned l1, unsigned l0, unsigned offset) {
  return ((uint64_t)(l2 & INDEX_MASK) << shift_for(2)) | ((uint64_t)(l1 & INDEX_MASK) << shift_for(1))
         | ((uint64_t)(l0 & INDEX_MASK) << shift_for(0)) | (offset & OFFSET_MASK);
}

int sysfs_sv39_canonical(uint64_t va) {
  /* Bit 38 is the top bit of the translated address; everything above it must copy it. An
   * arithmetic shift of a signed 64-bit value reproduces exactly that rule. */
  int64_t extended = (int64_t)(va << 25) >> 25;
  return (uint64_t)extended == va;
}

uint64_t sysfs_sv39_tables(const struct sysfs_sv39_run *runs, size_t count, uint64_t out[3]) {
  /* One root, always. Below it, a level-1 table is needed for each distinct gigabyte the runs
   * touch and a level-0 table for each distinct two megabytes — so the answer depends on where
   * the pages are and not at all on how many of them there are.
   *
   * Runs arrive sorted, so distinctness is a comparison with the previous chunk rather than a
   * set. That is not only cheaper; it is the reason this fits in a page of C. */
  uint64_t gigabytes = 0, leaves = 0;
  uint64_t previous_gib = 0, previous_2mib = 0;
  int started = 0;

  for (size_t i = 0; i < count; i++) {
    uint64_t first = runs[i].start;
    uint64_t last = first + runs[i].pages * SYSFS_SV39_PAGE_BYTES - 1;
    for (uint64_t chunk = first >> 21; chunk <= (last >> 21); chunk++) {
      uint64_t gib = chunk >> SYSFS_SV39_INDEX_BITS;
      if (!started || gib != previous_gib) {
        gigabytes++;
        previous_gib = gib;
      }
      if (!started || chunk != previous_2mib) {
        leaves++;
        previous_2mib = chunk;
      }
      started = 1;
    }
  }

  out[2] = 1;
  out[1] = gigabytes;
  out[0] = leaves;
  return out[0] + out[1] + out[2];
}
