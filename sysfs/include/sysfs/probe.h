/* Facts the machine will tell you about itself, asked in a way both targets can answer.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * This header is compiled twice from the same bytes: once against glibc on Linux (the `host`
 * target) and once against xv6's freestanding user library (the `xv6` target). That constraint
 * is why it looks the way it does.
 *
 *   - No #include of anything. xv6 user programs build with -ffreestanding -nostdlib and have
 *     no <stdint.h>, no <stddef.h> and no size_t. A header that needs libc cannot be shared.
 *   - __alignof__ rather than _Alignof. xv6 builds with -std=gnu99, where _Alignof does not yet
 *     exist; __alignof__ is a GNU extension both compilers have understood for twenty years.
 *   - Printing is the caller's problem. Both worlds have a printf(const char *, ...), but they
 *     are different functions with different capabilities, so this header hands rows to whatever
 *     the caller passes and formats them with %s and %d only — the intersection of what xv6's
 *     printf and glibc's printf both support.
 *
 * The output is one fact per line, `kind name value...`, because a format a shell can read with
 * `cut` is also a format a test can assert on without a parser.
 */

#ifndef SYSFS_PROBE_H
#define SYSFS_PROBE_H

#define SYSFS_PROBE_VERSION 1

/* Two structs with identical members in different orders. What the compiler does with them is
 * the whole of the alignment lesson, and it does it without being asked. */
struct sysfs_declaration_order {
  char first;
  int middle;
  char last;
};

struct sysfs_size_order {
  int middle;
  char first;
  char last;
};

/* One type's answer to "how many bytes, and where may it start?" */
#define SYSFS_TYPE_ROW(print, label, type) \
  print("type %s %d %d\n", label, (int)sizeof(type), (int)__alignof__(type))

/* The scalar types every later chapter reasons about. `long` and pointers are the interesting
 * ones: LP64 is a choice the ABI made, not a property of the hardware, and a reader who has
 * only ever used a 64-bit Linux has never seen it be anything else. */
#define SYSFS_PROBE_TYPES(print)                        \
  do {                                                  \
    SYSFS_TYPE_ROW(print, "char", char);                \
    SYSFS_TYPE_ROW(print, "short", short);              \
    SYSFS_TYPE_ROW(print, "int", int);                  \
    SYSFS_TYPE_ROW(print, "long", long);                \
    SYSFS_TYPE_ROW(print, "long_long", long long);      \
    SYSFS_TYPE_ROW(print, "pointer", void *);           \
    SYSFS_TYPE_ROW(print, "float", float);              \
    SYSFS_TYPE_ROW(print, "double", double);            \
  } while (0)

/* Where the compiler put each member, and how much of the struct is nothing at all. */
#define SYSFS_LAYOUT_ROW(print, label, type, payload)                       \
  print("layout %s %d %d %d\n", label, (int)sizeof(type),                   \
        (int)__alignof__(type), (int)(sizeof(type) - (unsigned)(payload)))

#define SYSFS_PROBE_LAYOUTS(print)                                                     \
  do {                                                                                 \
    SYSFS_LAYOUT_ROW(print, "declaration_order", struct sysfs_declaration_order,        \
                     sizeof(char) + sizeof(int) + sizeof(char));                        \
    SYSFS_LAYOUT_ROW(print, "size_order", struct sysfs_size_order,                      \
                     sizeof(int) + sizeof(char) + sizeof(char));                        \
  } while (0)

/* Byte order, asked of the machine rather than assumed.
 *
 * RISC-V is little-endian in every implementation anyone ships, but "everyone knows that" is the
 * kind of claim this book is not allowed to make. Reading the first byte of a known integer costs
 * three instructions and turns it into something measured. */
static inline int sysfs_is_little_endian(void) {
  unsigned int word = 1u;
  const unsigned char *bytes = (const unsigned char *)&word;
  return bytes[0] == 1u;
}

/* Byte offset of a member, without <stddef.h>'s offsetof and without forming a pointer from
 * the null address, which offsetof's classic hand-rolled definition does and which is undefined
 * behaviour the compiler is increasingly willing to act on. */
static inline int sysfs_offset_of_middle(void) {
  struct sysfs_declaration_order value = {0, 0, 0};
  const char *base = (const char *)&value;
  return (int)((const char *)&value.middle - base);
}

static inline int sysfs_offset_of_last(void) {
  struct sysfs_declaration_order value = {0, 0, 0};
  const char *base = (const char *)&value;
  return (int)((const char *)&value.last - base);
}

/* The same question of the other ordering. Both structs are reported rather than only the
 * wasteful one, because ch05 draws the bytes of each and a picture of where the holes are cannot
 * be assembled from half the offsets. */
static inline int sysfs_offset_of_size_first(void) {
  struct sysfs_size_order value = {0, 0, 0};
  const char *base = (const char *)&value;
  return (int)((const char *)&value.first - base);
}

static inline int sysfs_offset_of_size_last(void) {
  struct sysfs_size_order value = {0, 0, 0};
  const char *base = (const char *)&value;
  return (int)((const char *)&value.last - base);
}

/* Every fact this header knows, in one call. `world` is the caller's name for where it is
 * running: the point of the probe is that the two worlds answer identically, and a line saying
 * which one produced the answer is what lets a test check that. */
#define SYSFS_PROBE_ALL(print, world)                                          \
  do {                                                                         \
    print("sysprobe %d\n", SYSFS_PROBE_VERSION);                               \
    print("world %s\n", world);                                                \
    SYSFS_PROBE_TYPES(print);                                                  \
    SYSFS_PROBE_LAYOUTS(print);                                                \
    print("offset declaration_order.middle %d\n", sysfs_offset_of_middle());   \
    print("offset declaration_order.last %d\n", sysfs_offset_of_last());       \
    print("offset size_order.first %d\n", sysfs_offset_of_size_first());       \
    print("offset size_order.last %d\n", sysfs_offset_of_size_last());         \
    print("endian %s\n", sysfs_is_little_endian() ? "little" : "big");         \
    print("end sysprobe\n");                                                   \
  } while (0)

#endif /* SYSFS_PROBE_H */
