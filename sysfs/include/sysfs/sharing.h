/* Two counters, laid out two ways, for the chapter about what four cores cost each other.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The two structures below hold the same two counters and differ only in padding. In one they are
 * adjacent and therefore on the same cache line; in the other they are a line apart.
 *
 * Nothing in the C standard, and nothing in chapter 2, distinguishes them by anything but size.
 * Two threads incrementing one counter each will find them very different, and the difference is
 * not about correctness at all — both are correct, both are race-free, and one is far slower.
 * That is false sharing: two cores fighting over a line neither of them shares any *data* on.
 */

#ifndef SYSFS_SHARING_H
#define SYSFS_SHARING_H

#include <stdint.h>

/* The line size this layout is built around. ch15 measures it rather than assuming it, and a
 * reader whose machine differs should say so here and watch the figures move. */
#define SYSFS_LINE_BYTES 64

/* Adjacent. Two counters, sixteen bytes, one line. */
struct sysfs_packed {
  uint64_t a;
  uint64_t b;
};

/* A line apart. The padding is the entire difference and it is not small: the structure is eight
 * times the size for the same two numbers, which is the trade being made. */
struct sysfs_padded {
  uint64_t a;
  char pad[SYSFS_LINE_BYTES - sizeof(uint64_t)];
  uint64_t b;
  char tail[SYSFS_LINE_BYTES - sizeof(uint64_t)];
};

/* Whether two offsets within a structure land on the same line, which is the only question that
 * matters and is arithmetic rather than opinion. */
int sysfs_same_line(uint64_t first, uint64_t second);

#endif /* SYSFS_SHARING_H */
