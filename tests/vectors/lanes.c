/* Problems 21.1, 21.2 and 21.3 — the tail, the reassociation, and the bound.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository.
 *
 *   python3 -m pytest tests/vectors
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define V_MAX 64

/* -- Problem 21.1 -------------------------------------------------------------------------- */
/* What does width buy a loop of this length?
 *
 * A vector unit does `lanes` elements per instruction. A loop over `n` elements therefore runs
 * some number of full vector iterations and then finishes the remainder one element at a time —
 * the tail, which no width helps with.
 *
 * Assume one vector iteration costs the same as one scalar iteration, and return the speedup over
 * a scalar loop, times a hundred, rounded down. `n` and `lanes` are at least 1.
 *
 * The number to find is the one where this stops being worth doing. For a long loop the answer is
 * the lane count and the tail is a rounding error; for a short one the tail is the whole loop, and
 * the compiler will have emitted a great deal of code to achieve nothing. The vectors chapter's own table
 * shows one of these loops growing six times longer in exchange for being four times wider.
 */
uint64_t v_speedup_x100(uint64_t n, uint64_t lanes) {
  (void)n;
  (void)lanes;
  return 0; /* Problem 21.1 */
}

/* -- Problem 21.2 -------------------------------------------------------------------------- */
/* Why the compiler will not widen a floating-point sum without being asked.
 *
 * Add `n` floats left to right, the way the source says.
 */
float v_sum_sequential(const float *x, uint64_t n) {
  (void)x;
  (void)n;
  return 0.0f; /* Problem 21.2 */
}

/* Add the same floats the way a vector unit would: `lanes` accumulators running independently,
 * with element `i` going to accumulator `i % lanes`, and the accumulators added together left to
 * right at the end. All accumulators start at zero.
 *
 * Then find an input on which the two disagree — the test supplies one, so you will see it
 * whether you look for it or not — and the compiler's refusal stops being a limitation and
 * becomes the only defensible choice. Widening this loop changes the program's answer. It is
 * allowed to do that only if you say so, which is what `-ffast-math` says.
 */
float v_sum_lanewise(const float *x, uint64_t n, uint64_t lanes) {
  (void)x;
  (void)n;
  (void)lanes;
  return 0.0f; /* Problem 21.2 */
}

/* -- Problem 21.3 -------------------------------------------------------------------------- */
/* How much of the speedup you were allowed to have did you get?
 *
 * `scalar_ns` and `vector_ns` are what the two versions measured. `lanes` is the width, and so
 * the most the arithmetic could possibly have bought.
 *
 * Return the fraction of that bound achieved, as a percentage, rounded down.
 *
 * This is the number the vectors chapter asks for instead of a speedup, and the reason is that a speedup
 * printed alone invites you to be pleased with it. Printed as a fraction of what the width
 * allowed, it invites the only useful question — where the rest went — and the answer is usually
 * memory, a tail, or a loop that was never the bottleneck.
 *
 * A result over a hundred is not a triumph. It means something other than the width changed too,
 * and the comparison is no longer between two versions of one loop.
 */
uint64_t v_of_bound_x100(uint64_t scalar_ns, uint64_t vector_ns, uint64_t lanes) {
  (void)scalar_ns;
  (void)vector_ns;
  (void)lanes;
  return 0; /* Problem 21.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

/* Sums come back as the float's bit pattern rather than as a decimal. The whole problem is about
 * a difference in the last place, and printing that through a decimal conversion would be a way
 * of losing the thing being measured. */
static uint32_t bits_of(float value) {
  uint32_t bits;
  memcpy(&bits, &value, sizeof bits);
  return bits;
}

static uint64_t parse_floats(char *spec, float *out) {
  uint64_t n = 0;
  char *save = NULL;
  for (char *tok = strtok_r(spec, ".", &save); tok && n < V_MAX; tok = strtok_r(NULL, ".", &save))
    out[n++] = strtof(tok, NULL);
  return n;
}

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *arg = argv[i] + 1;
    switch (argv[i][0]) {
    case 'w': { /* w<n>,<lanes> */
      char *p = arg;
      uint64_t n = strtoull(p, &p, 10);
      uint64_t lanes = strtoull(*p == ',' ? p + 1 : p, NULL, 10);
      printf("speedup %d %llu\n", i - 1, (unsigned long long)v_speedup_x100(n, lanes));
      break;
    }
    case 's': { /* s<lanes>:<x0>.<x1>... */
      char *colon = strchr(arg, ':');
      if (!colon) {
        fprintf(stderr, "lanes: malformed sum %s\n", argv[i]);
        return 2;
      }
      *colon = '\0';
      uint64_t lanes = strtoull(arg, NULL, 10);
      float x[V_MAX];
      uint64_t n = parse_floats(colon + 1, x);
      printf("sum %d %08x %08x\n", i - 1, bits_of(v_sum_sequential(x, n)),
             bits_of(v_sum_lanewise(x, n, lanes)));
      break;
    }
    case 'b': { /* b<scalar_ns>,<vector_ns>,<lanes> */
      uint64_t v[3] = {0, 0, 0};
      char *p = arg;
      for (int k = 0; k < 3; k++) {
        v[k] = strtoull(p, &p, 10);
        if (*p == ',')
          p++;
      }
      printf("bound %d %llu\n", i - 1,
             (unsigned long long)v_of_bound_x100(v[0], v[1], v[2]));
      break;
    }
    default:
      fprintf(stderr, "lanes: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end lanes\n");
  return 0;
}
