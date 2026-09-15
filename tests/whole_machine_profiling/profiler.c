/* Problems 20.1, 20.2 and 20.3 — read a profile, and know what it cannot tell you.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository.
 *
 *   python3 -m pytest tests/whole_machine_profiling
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define P_MAX_NODES 64

/* -- Problem 20.1 -------------------------------------------------------------------------- */
/* Turn a flat profile into one you can act on.
 *
 * `parent[i]` is the index of the function that called node `i`, or -1 if `i` is a root. Every
 * parent index is smaller than its child's, so the array is already in an order you can use.
 * `exclusive[i]` is the samples attributed to node `i` itself — the profiler's own output, which
 * is exclusive by construction because a sample records one address.
 *
 * Write into `inclusive[i]` the samples spent in node `i` and everything it called.
 *
 * This is the first thing to do with any profile and the reason a flat one misleads. The symbol
 * at the top of an exclusive list is usually a leaf you did not write and cannot change; the
 * caller you *can* change is somewhere below it, holding a fraction of the total each, and only
 * the inclusive view puts it back together.
 */
void p_inclusive(const int *parent, const uint64_t *exclusive, int n, uint64_t *inclusive) {
  (void)parent;
  (void)exclusive;
  (void)n;
  (void)inclusive;
  for (int i = 0; i < n; i++)
    inclusive[i] = 0; /* Problem 20.1 */
}

/* -- Problem 20.2 -------------------------------------------------------------------------- */
/* How many samples before a share is worth believing?
 *
 * A profile is an estimate. A symbol holding a true share `p` of the running time collects, out
 * of `n` samples, a count whose standard error as a fraction is sqrt(p(1-p)/n).
 *
 * `share_per_mille` is p in parts per thousand, and `resolve_per_mille` is the width you want, in
 * the same units. Return the smallest `n` for which *two* standard errors fit inside that width,
 * rounded up.
 *
 * Do the arithmetic in integers. Working in per-mille, everything cancels into a single
 * expression over the two arguments, and the point of finding it is that it is small enough to do
 * in your head when a profile is on the screen in front of you.
 *
 * What the answer is for is deciding whether two runs differ. A symbol that moved by less than
 * this did not move.
 */
uint64_t p_samples_needed(uint64_t share_per_mille, uint64_t resolve_per_mille) {
  (void)share_per_mille;
  (void)resolve_per_mille;
  return 0; /* Problem 20.2 */
}

/* -- Problem 20.3 -------------------------------------------------------------------------- */
/* The artefact that makes a profile confidently wrong.
 *
 * A profiler that samples every `sample_period` cycles, running over a loop that takes exactly
 * `loop_period` cycles, does not sample the loop evenly. Sample `i` lands at position
 * `(i * sample_period) mod loop_period`, and that sequence does not visit every position.
 *
 * Return how many distinct positions in the loop the samples can ever land on. Both arguments are
 * at least 1.
 *
 * Work out what the answer depends on before writing it — it is one line, and it is the whole
 * reason real profilers do not use a fixed period. A profile that visits a handful of positions
 * out of thousands is not a low-resolution profile. It is a confident, repeatable, stable answer
 * to a question nobody asked.
 */
uint64_t p_distinct_positions(uint64_t sample_period, uint64_t loop_period) {
  (void)sample_period;
  (void)loop_period;
  return 0; /* Problem 20.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

/* Answers are keyed by the command's position, so a case whose arguments repeat still lands
 * somewhere the caller can find it. */

static int parse_tree(char *spec, int *parent, uint64_t *exclusive) {
  int n = 0;
  char *save = NULL;
  for (char *tok = strtok_r(spec, ".", &save); tok && n < P_MAX_NODES;
       tok = strtok_r(NULL, ".", &save)) {
    char *colon = strchr(tok, ':');
    if (!colon)
      return -1;
    *colon = '\0';
    parent[n] = atoi(tok);
    exclusive[n] = strtoull(colon + 1, NULL, 10);
    n++;
  }
  return n;
}

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *arg = argv[i] + 1;
    switch (argv[i][0]) {
    case 't': { /* t<parent>:<exclusive>.<parent>:<exclusive>... */
      int parent[P_MAX_NODES];
      uint64_t exclusive[P_MAX_NODES], inclusive[P_MAX_NODES];
      int n = parse_tree(arg, parent, exclusive);
      if (n < 0) {
        fprintf(stderr, "profiler: malformed tree %s\n", argv[i]);
        return 2;
      }
      p_inclusive(parent, exclusive, n, inclusive);
      printf("inclusive %d", i - 1);
      for (int k = 0; k < n; k++)
        printf(" %llu", (unsigned long long)inclusive[k]);
      printf("\n");
      break;
    }
    case 'n': { /* n<share_per_mille>,<resolve_per_mille> */
      char *p = arg;
      uint64_t share = strtoull(p, &p, 10);
      uint64_t resolve = strtoull(*p == ',' ? p + 1 : p, NULL, 10);
      printf("needed %d %llu\n", i - 1, (unsigned long long)p_samples_needed(share, resolve));
      break;
    }
    case 'a': { /* a<sample_period>,<loop_period> */
      char *p = arg;
      uint64_t sample = strtoull(p, &p, 10);
      uint64_t loop = strtoull(*p == ',' ? p + 1 : p, NULL, 10);
      printf("aliased %d %llu\n", i - 1,
             (unsigned long long)p_distinct_positions(sample, loop));
      break;
    }
    default:
      fprintf(stderr, "profiler: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end profiler\n");
  return 0;
}
