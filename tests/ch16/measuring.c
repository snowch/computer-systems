/* Problems 14.1, 14.2 and 14.3 — report it, repeat it enough, and throw away the warm-up.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * `sysfs/lib/timing.c` summarises a sample set and this asks you to write that summary yourself,
 * which is not a contradiction: the library is the book's instrument and this is your check on it.
 * The other two are not in the repository at all.
 *
 *   python3 -m pytest tests/ch16
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 14.1 -------------------------------------------------------------------------- */
/* Report the distribution rather than a number.
 *
 * `samples` holds `count` durations in no particular order. Write the minimum, the median, the
 * 90th percentile and the mean into the four outputs.
 *
 * Definitions, because they are where this goes wrong: the median of an even-length set is the
 * upper of the two middle values (not their average — a duration is a thing that happened, and
 * inventing one between two that did is how a benchmark reports a time nothing ever took). The
 * 90th percentile is the sample at index (count * 9) / 10 after sorting, clamped to the last.
 * The mean is the arithmetic mean, rounded down.
 *
 * `count` of zero leaves all four at zero.
 */
void m_summarise(const uint64_t *samples, uint64_t count, uint64_t *min, uint64_t *median,
                 uint64_t *p90, uint64_t *mean) {
  (void)samples;
  (void)count;
  *min = *median = *p90 = *mean = 0; /* Problem 14.1 */
}

/* -- Problem 14.2 -------------------------------------------------------------------------- */
/* How many times must the work be repeated inside one timed region?
 *
 * `work_ns` is roughly what one repetition costs and `clock_ns` is what reading the clock costs.
 * A timed region contains two clock reads, so the instrument contributes `clock_ns` to every
 * measurement regardless of how much work is inside it.
 *
 * Return the smallest number of repetitions for which the instrument is at most one part in
 * `budget` of the measurement — that is, for which clock_ns * budget <= work_ns * repetitions.
 *
 * Return 1 if one repetition already suffices, and 0 if `work_ns` is zero, which is a question
 * without an answer rather than a number.
 */
uint64_t m_repetitions(uint64_t work_ns, uint64_t clock_ns, uint64_t budget) {
  (void)work_ns;
  (void)clock_ns;
  (void)budget;
  return 1; /* Problem 14.2 */
}

/* -- Problem 14.3 -------------------------------------------------------------------------- */
/* How many leading samples are warm-up?
 *
 * A benchmark's first measurements are slower: caches are cold, pages are unmapped, the branch
 * predictor knows nothing. Including them makes every statistic wrong in the same direction.
 *
 * `samples` are in the order they were taken. Return the smallest `k` for which both of these
 * hold, and `count` if there is no such `k`:
 *
 *   - every sample from index `k` onwards is at most `tolerance` percent above the minimum of the
 *     samples from `k` onwards — the tail has settled;
 *   - every sample before index `k` is outside that band — the part you are discarding was
 *     actually slow.
 *
 * The second condition is the one that makes this mean something, and leaving it out is the
 * obvious mistake. Without it, a set with one slow sample in the middle can be "warmed up" by
 * discarding everything before the spike, which throws away good measurements to hide a bad one.
 * Warm-up is a property of position; a spike in the middle is interference, they are not the same
 * thing, and a set that has both cannot be fixed by trimming a prefix at all.
 */
uint64_t m_warmup(const uint64_t *samples, uint64_t count, uint64_t tolerance) {
  (void)samples;
  (void)count;
  (void)tolerance;
  return 0; /* Problem 14.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

#define MAX_SAMPLES 256

static uint64_t parse(char *text, uint64_t *out) {
  uint64_t n = 0;
  for (char *p = text; *p && n < MAX_SAMPLES;) {
    out[n++] = strtoull(p, &p, 10);
    if (*p == '.')
      p++;
  }
  return n;
}

int main(int argc, char **argv) {
  uint64_t samples[MAX_SAMPLES];

  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    switch (argv[i][0]) {
    case 's': { /* s<index>,<sample>.<sample>... */
      if (comma == NULL)
        return 2;
      *comma = '\0';
      uint64_t n = parse(comma + 1, samples);
      uint64_t min, median, p90, mean;
      m_summarise(samples, n, &min, &median, &p90, &mean);
      printf("summary %s %llu %llu %llu %llu\n", argv[i] + 1, (unsigned long long)min,
             (unsigned long long)median, (unsigned long long)p90, (unsigned long long)mean);
      break;
    }
    case 'r': { /* r<work>,<clock>,<budget> */
      if (comma == NULL)
        return 2;
      char *second = strchr(comma + 1, ',');
      if (second == NULL)
        return 2;
      printf("repetitions %s %llu\n", argv[i] + 1,
             (unsigned long long)m_repetitions(strtoull(argv[i] + 1, NULL, 10),
                                               strtoull(comma + 1, NULL, 10),
                                               strtoull(second + 1, NULL, 10)));
      break;
    }
    case 'w': { /* w<index>,<tolerance>,<sample>.<sample>... */
      if (comma == NULL)
        return 2;
      char *second = strchr(comma + 1, ',');
      if (second == NULL)
        return 2;
      *comma = '\0';
      uint64_t tolerance = strtoull(comma + 1, NULL, 10);
      uint64_t n = parse(second + 1, samples);
      printf("warmup %s %llu\n", argv[i] + 1, (unsigned long long)m_warmup(samples, n, tolerance));
      break;
    }
    default:
      fprintf(stderr, "measuring: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end measuring\n");
  return 0;
}
