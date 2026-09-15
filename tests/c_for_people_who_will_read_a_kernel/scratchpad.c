/* Problem 3.2 — a function that works until it is called twice.
 *
 * `describe()` turns a small number into text. It is correct in isolation and wrong in use: the
 * caller below gets two descriptions and prints them, and one of them is not what it asked for.
 *
 * Find out why, and fix `describe()` so that main() prints two different descriptions. You may
 * change describe() and its declaration however you like, including what it returns and what
 * arguments it takes. You may not change main().
 *
 * This is not a contrived bug. The C library did exactly this for years, and some of it still
 * does — which is why there are functions in it with an `_r` on the end.
 */

#include <stdio.h>

static char scratch[32];

/* Problem 3.2 — this is the function to fix. */
const char *describe(int value) {
  const char *word = value < 0 ? "negative" : (value == 0 ? "zero" : "positive");
  int index = 0;
  while (word[index] && index < 31) {
    scratch[index] = word[index];
    index++;
  }
  scratch[index] = '\0';
  return scratch;
}

int main(void) {
  const char *first = describe(-5);
  const char *second = describe(7);
  printf("%s %s\n", first, second);
  return 0;
}
