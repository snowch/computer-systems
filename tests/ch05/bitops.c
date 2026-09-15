/* Problem 2.1 — two operations this book's library does not contain.
 *
 * Fill in both. Neither is in sysfs/lib/bits.c, so there is nothing to copy; the properties the
 * test checks are in the Problems section of chapter 2, and they are the definition.
 *
 * Build and check with:  python3 -m pytest tests/ch05/test_problem_1_bitops.py
 */

#include <stdio.h>

#define WORD_BITS (sizeof(unsigned long) * 8)

/* The same bytes in the opposite order: the lowest byte becomes the highest.
 *
 * Not the same as reversing the bits — the bits inside each byte keep their order. Chapter 2's
 * section on byte order says why a machine ever needs this. */
unsigned long reader_swap_bytes(unsigned long word) {
  (void)word;
  return 0; /* Problem 2.1 */
}

/* The index of the lowest set bit, counting from 0.
 *
 * For a word with no bits set there is no such index, so return WORD_BITS — a value no real
 * answer can take, which is a better way to say "none" than picking one that can. */
unsigned reader_lowest_set_bit(unsigned long word) {
  (void)word;
  return 0; /* Problem 2.1 */
}

/* The harness. Reads one operation and one argument per line and prints the answer, so the test
 * can ask for as many cases as it likes without recompiling. */
int main(void) {
  char op[32];
  unsigned long argument;
  while (scanf("%31s %lu", op, &argument) == 2) {
    if (op[0] == 's') {
      printf("%lu\n", reader_swap_bytes(argument));
    } else {
      printf("%u\n", reader_lowest_set_bit(argument));
    }
  }
  return 0;
}
