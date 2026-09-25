/* Keeping every sample. See sysfs/include/sysfs/distribution.h for why.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 */

#include "sysfs/distribution.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/timing.h"

/* Big enough to exceed any last-level cache this book is likely to meet, and touched at a stride
 * that defeats a prefetcher following it. Sized rather than measured on purpose: the memory
 * chapter measures a hierarchy, and a harness that had to measure one before it could run would
 * make every chapter depend on that one working. */
#define EVICT_BYTES (32u * 1024u * 1024u)
#define EVICT_STRIDE 64u

static volatile unsigned char evict_sink;

void sysfs_evict_caches(void) {
  unsigned char *buffer = malloc(EVICT_BYTES);
  if (!buffer)
    return; /* a cold run we could not make cold is reported by the runner, not faked here */

  for (size_t i = 0; i < EVICT_BYTES; i += EVICT_STRIDE)
    buffer[i] = (unsigned char)(i >> 6);
  for (size_t i = 0; i < EVICT_BYTES; i += EVICT_STRIDE)
    evict_sink = (unsigned char)(evict_sink + buffer[i]);

  free(buffer);
}

int sysfs_parse_run_spec(int argc, char **argv, struct sysfs_run_spec *out) {
  int have_warmup = 0, have_runs = 0, have_mode = 0, have_raw = 0;
  memset(out, 0, sizeof *out);

  for (int i = 1; i + 1 < argc; i += 2) {
    const char *flag = argv[i], *value = argv[i + 1];
    if (strcmp(flag, "--warmup") == 0) {
      out->warmup_runs = strtoull(value, NULL, 10);
      have_warmup = 1;
    } else if (strcmp(flag, "--runs") == 0) {
      out->runs = strtoull(value, NULL, 10);
      have_runs = 1;
    } else if (strcmp(flag, "--mode") == 0) {
      if (strcmp(value, "cold") == 0)
        out->cold = 1;
      else if (strcmp(value, "warm") == 0)
        out->cold = 0;
      else {
        fprintf(stderr, "mode must be 'cold' or 'warm', not '%s'\n", value);
        return 1;
      }
      have_mode = 1;
    } else if (strcmp(flag, "--raw") == 0) {
      out->raw_path = value;
      have_raw = 1;
    }
  }

  /* Every one of these is required. The message says which is missing rather than printing a
   * usage line, because the reader who hits this is mid-experiment and wants the one word. */
  if (!have_warmup || !have_runs || !have_mode || !have_raw) {
    fprintf(stderr, "missing:%s%s%s%s\n", have_warmup ? "" : " --warmup N",
            have_runs ? "" : " --runs N", have_mode ? "" : " --mode cold|warm",
            have_raw ? "" : " --raw PATH");
    return 1;
  }
  if (out->runs == 0) {
    fprintf(stderr, "--runs 0 measures nothing\n");
    return 1;
  }
  return 0;
}

int sysfs_write_samples(const char *path, const uint64_t *samples, uint64_t count) {
  FILE *out = fopen(path, "w");
  if (!out)
    return 1;
  for (uint64_t i = 0; i < count; i++)
    fprintf(out, "%llu\n", (unsigned long long)samples[i]);
  return fclose(out) != 0;
}

int sysfs_run_distribution(const struct sysfs_run_spec *spec, void (*work)(void *),
                           void *context) {
  uint64_t *samples = malloc((size_t)spec->runs * sizeof *samples);
  if (!samples)
    return 1;

  /* Warm-up is discarded rather than recorded, and the count is stamped beside the result: the
   * chapter's point is that the first samples are slow because they are first, so which ones were
   * thrown away is part of what the number means. */
  for (uint64_t i = 0; i < spec->warmup_runs; i++) {
    if (spec->cold)
      sysfs_evict_caches();
    work(context);
  }

  for (uint64_t i = 0; i < spec->runs; i++) {
    if (spec->cold)
      sysfs_evict_caches();
    uint64_t start = sysfs_now_ns();
    work(context);
    samples[i] = sysfs_now_ns() - start;
  }

  int failed = sysfs_write_samples(spec->raw_path, samples, spec->runs);
  free(samples);
  return failed;
}
