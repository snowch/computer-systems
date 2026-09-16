/* One program, two ways round the same data, for the crossing between the book's two targets.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The crossing chapter needs a program that Parts III and IV explain completely and whose cost they do not predict
 * at all. These two functions add up exactly the same numbers and return exactly the same answer.
 * One walks an array from beginning to end; the other follows a chain through the same array,
 * visiting every element exactly once, in an order arranged so that no two consecutive visits are
 * near each other.
 *
 * Structurally they are nearly the same function: the same additions, the same loop, one extra
 * load. Everything Part IV can say about one, it says about the other. What separates them is not
 * visible in any of it.
 *
 * The bodies arrive through a macro rather than a library, for stages.h's reason: an xv6 user
 * program is one translation unit, so there is nowhere to put a second object. The macro is what
 * lets the host build, the kernel build and the disassembly all compile the same bytes.
 */

#ifndef SYSFS_BRIDGE_H
#define SYSFS_BRIDGE_H

/* `next` is an index rather than a pointer so the structure has the same size and layout on both
 * targets — which is the representing-information chapter's subject, and the reason this comparison is allowed to be made. */
struct sysfs_cell {
  long value;
  long next;
};

#define SYSFS_BRIDGE_DEFINE                                                   \
  /* A stride that visits everything. Any odd number coprime with count       \
   * closes the cycle; a little under a third keeps consecutive visits far    \
   * apart without being a power of two, which would land them on a small set \
   * of cache sets — a distinction the memory-hierarchy chapter has the equipment to explain. */      \
  long sysfs_bridge_stride(long count) {                                      \
    long stride = count / 3;                                                  \
    if (stride < 1)                                                           \
      return 1;                                                               \
    if ((stride & 1) == 0)                                                    \
      stride++;                                                               \
    while (count % stride == 0)                                               \
      stride += 2;                                                            \
    return stride;                                                            \
  }                                                                           \
                                                                              \
  void sysfs_bridge_fill(struct sysfs_cell *cells, long count, long stride) { \
    long at = 0;                                                              \
    for (long i = 0; i < count; i++) {                                        \
      long next = (at + stride) % count;                                      \
      cells[at].value = at + 1;                                               \
      cells[at].next = next;                                                  \
      at = next;                                                              \
    }                                                                         \
  }                                                                           \
                                                                              \
  /* Every value, in the order they are stored. */                            \
  long sysfs_bridge_sequential(const struct sysfs_cell *cells, long count) {  \
    long total = 0;                                                           \
    for (long i = 0; i < count; i++)                                          \
      total += cells[i].value;                                                \
    return total;                                                             \
  }                                                                           \
                                                                              \
  /* Every value, in the order the chain gives them. Same values, same total, \
   * same number of additions, and one more load to find out where to go. */  \
  long sysfs_bridge_chased(const struct sysfs_cell *cells, long count) {      \
    long total = 0;                                                           \
    long at = 0;                                                              \
    for (long i = 0; i < count; i++) {                                        \
      total += cells[at].value;                                               \
      at = cells[at].next;                                                    \
    }                                                                         \
    return total;                                                             \
  }

long sysfs_bridge_stride(long count);
void sysfs_bridge_fill(struct sysfs_cell *cells, long count, long stride);
long sysfs_bridge_sequential(const struct sysfs_cell *cells, long count);
long sysfs_bridge_chased(const struct sysfs_cell *cells, long count);

#endif /* SYSFS_BRIDGE_H */
