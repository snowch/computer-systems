/* Problems 15.1, 15.2 and 15.3 — read the machine out of the curve, then predict with it.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository. `sysfs/bench/hierarchy.c` produces the curves and draws no
 * conclusions from them, which is the division of labour on purpose: reading a hierarchy out of a
 * latency curve is the skill, and a tool that did it for you would remove it.
 *
 *   python3 -m pytest tests/ch22
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 15.1 -------------------------------------------------------------------------- */
/* Where does this curve step?
 *
 * `x` and `ns` hold `count` points of a latency curve, in increasing order of x. A step is a point
 * whose latency is at least `factor` tenths higher than the point before it — so `factor` of 15
 * means "half again as slow".
 *
 * Write the x-values at which the curve steps into `steps`, in order, and return how many there
 * were. Never write more than `capacity`.
 *
 * On a real machine these are the level boundaries, and the x-value of a step is the size at which
 * the working set stopped fitting — that is, the size of the level below it.
 */
uint64_t h_steps(const uint64_t *x, const uint64_t *ns, uint64_t count, uint64_t factor,
                 uint64_t *steps, uint64_t capacity) {
  (void)x;
  (void)ns;
  (void)count;
  (void)factor;
  (void)steps;
  (void)capacity;
  return 0; /* Problem 15.1 */
}

/* -- Problem 15.2 -------------------------------------------------------------------------- */
/* What is the line size?
 *
 * A stride curve is flat while consecutive visits share a cache line and rises once they stop.
 * Given the same arrays, return the stride at which it first rises — which is the line size — or 0
 * if it never does.
 *
 * You may use h_steps. The interesting part is not the search; it is that this number is a
 * property of the machine that no amount of reading the source of a program will tell you, and
 * that it is the same number for every level.
 */
uint64_t h_line_size(const uint64_t *stride, const uint64_t *ns, uint64_t count, uint64_t factor) {
  (void)stride;
  (void)ns;
  (void)count;
  (void)factor;
  return 0; /* Problem 15.2 */
}

/* -- Problem 15.3 -------------------------------------------------------------------------- */
/* How many cache lines does this loop touch?
 *
 * A loop reads `elements` items of `element_bytes` each, `stride_elements` apart, from an array
 * laid out contiguously and aligned to a line. The cache line is `line_bytes`.
 *
 * Return the number of distinct lines touched.
 *
 * The two cases worth getting right: a stride smaller than a line means several elements share a
 * line and the count is far lower than the element count; a stride of a line or more means one
 * line each, and making the stride larger still does not make it worse. That ceiling is why a
 * loop can get dramatically slower as its stride grows and then stop getting worse, which is a
 * shape that surprises people the first time they measure it.
 */
uint64_t h_lines_touched(uint64_t elements, uint64_t element_bytes, uint64_t stride_elements,
                         uint64_t line_bytes) {
  (void)elements;
  (void)element_bytes;
  (void)stride_elements;
  (void)line_bytes;
  return 0; /* Problem 15.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

#define MAX_POINTS 64

static uint64_t parse(char *text, uint64_t *out) {
  uint64_t n = 0;
  for (char *p = text; *p && n < MAX_POINTS;) {
    out[n++] = strtoull(p, &p, 10);
    if (*p == '.')
      p++;
  }
  return n;
}

int main(int argc, char **argv) {
  uint64_t xs[MAX_POINTS], ys[MAX_POINTS], steps[MAX_POINTS];

  for (int i = 1; i < argc; i++) {
    char *first = strchr(argv[i], ',');
    if (first == NULL)
      return 2;
    *first = '\0';
    switch (argv[i][0]) {
    case 's':   /* s<index>,<factor>,<x>.<x>...,<ns>.<ns>... */
    case 'l': { /* same shape */
      char *second = strchr(first + 1, ',');
      if (second == NULL)
        return 2;
      *second = '\0';
      char *third = strchr(second + 1, ',');
      if (third == NULL)
        return 2;
      *third = '\0';
      uint64_t factor = strtoull(first + 1, NULL, 10);
      uint64_t n = parse(second + 1, xs);
      parse(third + 1, ys);
      if (argv[i][0] == 's') {
        uint64_t found = h_steps(xs, ys, n, factor, steps, MAX_POINTS);
        printf("steps %s %llu", argv[i] + 1, (unsigned long long)found);
        for (uint64_t k = 0; k < found; k++)
          printf(" %llu", (unsigned long long)steps[k]);
        printf("\n");
      } else {
        printf("line %s %llu\n", argv[i] + 1,
               (unsigned long long)h_line_size(xs, ys, n, factor));
      }
      break;
    }
    case 't': { /* t<elements>,<element_bytes>,<stride>,<line> */
      uint64_t v[4] = {0, 0, 0, 0};
      v[0] = strtoull(argv[i] + 1, NULL, 10);
      char *p = first + 1;
      for (int k = 1; k < 4; k++)
        v[k] = strtoull(p, &p, 10), p += (*p == ',');
      printf("lines %llu %llu\n", (unsigned long long)v[0],
             (unsigned long long)h_lines_touched(v[0], v[1], v[2], v[3]));
      break;
    }
    default:
      fprintf(stderr, "hierarchy: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end hierarchy\n");
  return 0;
}
