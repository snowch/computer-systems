/* Bit-level operations the rest of the book reuses, and the types they are careful about.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * No <stdint.h>. These are compiled for the host target, but ch07 wants the alignment helpers
 * inside an xv6 program later and a header that needs libc cannot be shared — the same
 * constraint probe.h explains at length. `unsigned long` is 64-bit under LP64 on both of the
 * book's architectures, which ch00 measured rather than assumed.
 */

#ifndef SYSFS_BITS_H
#define SYSFS_BITS_H

/* How many bits are set. */
unsigned sysfs_popcount(unsigned long word);

/* The same bits, in the opposite order: bit 0 becomes the top bit. */
unsigned long sysfs_reverse_bits(unsigned long word);

/* The smallest power of two that is not less than `value`; 0 for 0, and 0 on overflow, because
 * the alternative is returning a lie and ch02 is a chapter about not doing that. */
unsigned long sysfs_round_up_pow2(unsigned long value);

/* Whether `value` is a multiple of `alignment`. `alignment` must be a power of two — ch07 relies
 * on this and ch07's alignments always are. */
int sysfs_is_aligned(unsigned long value, unsigned long alignment);

#endif /* SYSFS_BITS_H */
