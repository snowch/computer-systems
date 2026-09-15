/* vectorcost — what widening a loop actually bought, on the machine being measured.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The same five loops chapter 23 disassembles. This source is built twice, at the book's own
 * optimisation level and at the one where this compiler starts widening, and the difference
 * between the two runs is the measurement. Nothing here knows which build it is: that is the
 * runner's business, and a workload that behaved differently depending on its flags would be
 * measuring itself.
 */

#include <stdio.h>
#include <stdlib.h>

#include "sysfs/timing.h"
#include "sysfs/vectors.h"

#define COUNT 65536
#define RUNS 200

static float in[COUNT], out[COUNT];
static int32_t wide_in[COUNT];
static int32_t index_of[COUNT];
static uint64_t samples[RUNS];

static uint64_t best(void (*body)(void)) {
  for (int i = 0; i < RUNS; i++) {
    uint64_t before = sysfs_now_ns();
    body();
    samples[i] = sysfs_now_ns() - before;
  }
  return sysfs_summarise(samples, RUNS).min;
}

static volatile float sink_f;
static volatile int64_t sink_i;

static void do_scale(void) { sysfs_vec_scale(out, in, 1.5f, COUNT); }
static void do_sum_i32(void) { sink_i = sysfs_vec_sum_i32(wide_in, COUNT); }
static void do_sum_f32(void) { sink_f = sysfs_vec_sum_f32(in, COUNT); }
static void do_gather(void) { sysfs_vec_gather(out, in, index_of, COUNT); }
static void do_running(void) { sysfs_vec_running(out, in, COUNT); }

int main(void) {
  for (uint64_t i = 0; i < COUNT; i++) {
    in[i] = (float)(i % 1000) * 0.5f;
    wide_in[i] = (int32_t)(i % 1000);
    index_of[i] = (int32_t)((i * 7919) % COUNT);
  }

  struct {
    const char *name;
    void (*body)(void);
    unsigned element_bits;
  } loops[] = {
      {"sysfs_vec_scale", do_scale, 32},   {"sysfs_vec_sum_i32", do_sum_i32, 32},
      {"sysfs_vec_sum_f32", do_sum_f32, 32}, {"sysfs_vec_gather", do_gather, 32},
      {"sysfs_vec_running", do_running, 32},
  };

  printf("vectorcost elements %d\n", COUNT);
  for (unsigned i = 0; i < sizeof loops / sizeof loops[0]; i++)
    printf("loop %s total_ns %llu element_bits %u\n", loops[i].name,
           (unsigned long long)best(loops[i].body), loops[i].element_bits);
  printf("end vectorcost\n");
  return 0;
}
