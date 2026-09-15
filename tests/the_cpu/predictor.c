/* Problems 17.2 and 17.3 — the critical path, and what a predictor actually does.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Neither is in the repository.
 *
 *   python3 -m pytest tests/the_cpu
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 17.2 -------------------------------------------------------------------------- */
/* How long is the critical path?
 *
 * A loop adds `elements` values into `accumulators` independent running totals, taking them in
 * turn, and combines the accumulators at the end with a tree of additions.
 *
 * Return the number of additions on the longest chain of dependent additions — the critical path.
 * Each accumulator's chain is its share of the elements; combining `accumulators` totals takes
 * ceil(log2(accumulators)) further additions, and those are on the path too.
 *
 * The number of additions performed does not change with `accumulators`. This does, and it is the
 * one the machine's throughput follows.
 *
 * Notice what this model then predicts: that more accumulators are always better, right down to
 * one element each. On a real machine they are not, and what stops it is nowhere in this formula —
 * accumulators live in registers, there are a fixed number of those, and past that point they
 * spill to memory and chapter 15's subject takes over. A model that is right about what it models
 * and silent about what limits it is the usual kind, and knowing which is which is the skill.
 */
uint64_t p_critical_path(uint64_t elements, uint64_t accumulators) {
  (void)elements;
  (void)accumulators;
  return 0; /* Problem 17.2 */
}

/* -- Problem 17.3 -------------------------------------------------------------------------- */
/* How many of these branches does a two-bit predictor get wrong?
 *
 * `outcomes` is a string of 'T' and 'N'. The predictor is a saturating two-bit counter starting at
 * 0 (strongly not-taken), with states 0 and 1 predicting not-taken and 2 and 3 predicting taken.
 * A taken branch increments the counter and a not-taken one decrements it, both saturating.
 *
 * Return the number of predictions that were wrong.
 *
 * The reason two bits rather than one is the alternating pattern: a one-bit predictor gets every
 * single branch of "TNTNTN" wrong, and a two-bit one gets about half. The reason two bits rather
 * than three is that nobody could measure the difference, which is a better argument than it
 * sounds.
 */
uint64_t p_mispredicts(const char *outcomes) {
  (void)outcomes;
  return 0; /* Problem 17.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    switch (argv[i][0]) {
    case 'c': /* c<elements>,<accumulators> */
      if (comma == NULL)
        return 2;
      *comma = '\0';
      printf("path %s,%s %llu\n", argv[i] + 1, comma + 1,
             (unsigned long long)p_critical_path(strtoull(argv[i] + 1, NULL, 10),
                                                 strtoull(comma + 1, NULL, 10)));
      break;
    case 'm': /* m<outcomes> */
      printf("mispredicts %s %llu\n", argv[i] + 1,
             (unsigned long long)p_mispredicts(argv[i] + 1));
      break;
    default:
      fprintf(stderr, "predictor: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end predictor\n");
  return 0;
}
