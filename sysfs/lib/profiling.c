/* Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE. */

#include "sysfs/profiling.h"

void sysfs_tally_fill(uint64_t seed, uint32_t *raw, uint64_t n) {
  uint64_t state = seed | 1u;
  for (uint64_t i = 0; i < n; i++) {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    raw[i] = (uint32_t)(state >> 16);
  }
}

uint64_t sysfs_tally_decode(const uint32_t *raw, uint64_t n, uint32_t *keys, uint32_t entries) {
  uint64_t taken = 0;
  for (uint64_t i = 0; i < n; i++) {
    uint32_t v = raw[i];
    uint32_t mixed = (v ^ (v >> 11)) * 2654435761u;
    /* A conditional over a quantity that is almost always on one side of the test. It is here to
     * be seen in the source and found innocent by the measurement. */
    if ((mixed >> 24) != 0) {
      mixed ^= mixed >> 15;
      taken++;
    }
    keys[i] = mixed % entries;
  }
  return taken;
}

uint64_t sysfs_tally_scatter(const uint32_t *keys, uint64_t n, uint32_t *table, uint32_t entries) {
  for (uint32_t e = 0; e < entries; e++)
    table[e] = 0;
  for (uint64_t i = 0; i < n; i++)
    table[keys[i]]++;

  uint64_t sum = 0;
  for (uint32_t e = 0; e < entries; e++)
    sum += (uint64_t)table[e] * (e + 1);
  return sum;
}

uint64_t sysfs_tally_partitioned(const uint32_t *keys, uint64_t n, uint32_t *table,
                                 uint32_t entries, uint32_t buckets, uint32_t *scratch,
                                 uint32_t *offsets) {
  uint32_t slice = entries / buckets;

  for (uint32_t b = 0; b <= buckets; b++)
    offsets[b] = 0;
  for (uint64_t i = 0; i < n; i++)
    offsets[keys[i] / slice + 1]++;
  for (uint32_t b = 0; b < buckets; b++)
    offsets[b + 1] += offsets[b];

  /* `offsets` is consumed as a cursor here and rebuilt below, so that the second pass can find
   * where each run ends without a second array. */
  for (uint64_t i = 0; i < n; i++)
    scratch[offsets[keys[i] / slice]++] = keys[i];
  for (uint32_t b = buckets; b > 0; b--)
    offsets[b] = offsets[b - 1];
  offsets[0] = 0;

  for (uint32_t e = 0; e < entries; e++)
    table[e] = 0;
  for (uint32_t b = 0; b < buckets; b++)
    for (uint32_t i = offsets[b]; i < offsets[b + 1]; i++)
      table[scratch[i]]++;

  uint64_t sum = 0;
  for (uint32_t e = 0; e < entries; e++)
    sum += (uint64_t)table[e] * (e + 1);
  return sum;
}
