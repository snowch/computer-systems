/* Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE. */

#include "sysfs/vectors.h"

void sysfs_vec_scale(float *out, const float *in, float k, uint64_t n) {
  for (uint64_t i = 0; i < n; i++)
    out[i] = in[i] * k;
}

int64_t sysfs_vec_sum_i32(const int32_t *x, uint64_t n) {
  int64_t total = 0;
  for (uint64_t i = 0; i < n; i++)
    total += x[i];
  return total;
}

float sysfs_vec_sum_f32(const float *x, uint64_t n) {
  float total = 0.0f;
  for (uint64_t i = 0; i < n; i++)
    total += x[i];
  return total;
}

void sysfs_vec_gather(float *out, const float *in, const int32_t *index, uint64_t n) {
  for (uint64_t i = 0; i < n; i++)
    out[i] = in[index[i]];
}

void sysfs_vec_running(float *out, const float *in, uint64_t n) {
  float carried = 0.0f;
  for (uint64_t i = 0; i < n; i++) {
    carried = carried * 0.5f + in[i];
    out[i] = carried;
  }
}
