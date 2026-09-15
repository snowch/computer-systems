/* firstc — one complete C program, before any of the parts.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Chapter 1 shows this file whole, because until now every piece of C in this book has been a
 * fragment lifted out of somewhere larger. A reader who has never written C has never seen where
 * the pieces go.
 *
 * It is also the chapter's first measurement, and it is deliberately not an address. Printing one
 * would show a number that differs on every run and means nothing on its own; what is worth
 * seeing is the *relationships* between addresses, which are the same every time:
 *
 *   that `*&x` is `x` again, so `&` and `*` undo each other;
 *   that `p + 1` moves by the size of what `p` points at, and by nothing else.
 *
 *   cc -o firstc firstc.c && ./firstc
 */

#include <stdint.h>
#include <stdio.h>

int main(void) {
  int value = 42;

  /* `&value` is where it lives; `*` goes back to what lives there. The two are inverses, and
   * this line is the whole of that claim. */
  int *where = &value;
  printf("firstc value %d roundtrip %d\n", value, *where);

  /* Two arrays, same length, different element type. The distance between one element and the
   * next is not one byte — it is one *element*, and how big an element is comes from the type. */
  int32_t narrow[2];
  int64_t wide[2];
  printf("firstc step int32 %td\n", (char *)&narrow[1] - (char *)&narrow[0]);
  printf("firstc step int64 %td\n", (char *)&wide[1] - (char *)&wide[0]);

  printf("end firstc\n");
  return 0;
}
