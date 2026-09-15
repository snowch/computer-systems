/* The bit operations, written out rather than called for.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Every one of these has a builtin or an instruction that does it in one go, and later chapters
 * will use those. They are written the long way here because ch10 is about what a machine word
 * *is*, and a function you wrote is a better place to learn that than an intrinsic you called.
 * ch11 disassembles both and the difference is not small.
 */

#include "sysfs/bits.h"

#define WORD_BITS (sizeof(unsigned long) * 8)

unsigned sysfs_popcount(unsigned long word) {
  unsigned set = 0;
  while (word) {
    /* Clearing the lowest set bit each time, so this runs once per set bit rather than once per
     * bit in the word. Worth knowing as a shape: `x & (x - 1)` is the single most reused
     * bit-twiddling identity in this book. */
    word &= word - 1;
    set++;
  }
  return set;
}

unsigned long sysfs_reverse_bits(unsigned long word) {
  unsigned long reversed = 0;
  for (unsigned index = 0; index < WORD_BITS; index++) {
    reversed = (reversed << 1) | (word & 1);
    word >>= 1;
  }
  return reversed;
}

unsigned long sysfs_round_up_pow2(unsigned long value) {
  if (value == 0) {
    return 0;
  }
  unsigned long result = 1;
  while (result < value) {
    /* The overflow check has to come before the shift, not after: once the top bit shifts out
     * there is nothing left to notice it by. Returning 0 says "no such power of two fits",
     * which a caller can test; wrapping silently to 0 would say the same thing by accident. */
    if (result > (~0UL >> 1)) {
      return 0;
    }
    result <<= 1;
  }
  return result;
}

int sysfs_is_aligned(unsigned long value, unsigned long alignment) {
  return (value & (alignment - 1)) == 0;
}
