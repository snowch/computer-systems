/* Problems 19.1, 19.2 and 19.3 — measure it right, bound it, and know which fault you have.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository.
 *
 *   python3 -m pytest tests/ch21
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* -- Problem 19.1 -------------------------------------------------------------------------- */
/* What will this harness report, and what is the truth?
 *
 * A harness times `iterations` calls of something that really costs `call_ns`. Reading the clock
 * costs `clock_ns`, and exactly one clock read falls inside each interval the harness times —
 * the one that opens it.
 *
 * `inside` says where the reads are:
 *
 *   inside = 1   read the clock on both sides of *every* call, and report the mean interval
 *   inside = 0   read it once before the loop and once after, and divide the whole by
 *                `iterations`
 *
 * Return what the harness reports as the cost of one call, in nanoseconds, rounded down.
 * `iterations` is at least 1.
 *
 * This is the easiest of chapter 19's traps to fall into. On a machine where the thing being
 * timed is cheap, an instrument inside the loop is added to every call and never divided by
 * anything, and what comes out is a confident measurement of `clock_gettime`.
 */
uint64_t o_reported_ns(uint64_t call_ns, uint64_t clock_ns, uint64_t iterations, int inside) {
  (void)call_ns;
  (void)clock_ns;
  (void)iterations;
  (void)inside;
  return 0; /* Problem 19.1 */
}

/* -- Problem 19.2 -------------------------------------------------------------------------- */
/* What does Part III's model say this cannot be cheaper than?
 *
 * `instructions` is the length of the trap path chapter 6 counted. `ipc_x100` is the
 * instructions-per-cycle the machine sustains on it, times a hundred, so 150 means 1.5. `mhz` is
 * the clock in megahertz.
 *
 * Return the lower bound on one system call in nanoseconds, rounded down — the instructions have
 * to be executed, and they cannot go faster than the machine retires them. Divide once, at the
 * end: rounding twice turns a bound into an estimate.
 *
 * Then remember what it leaves out: everything the kernel does after the path, the cache and TLB
 * the call disturbs, and the return. A measurement that comes in *under* the bound means the
 * model is wrong. A measurement ten times over it means the model was never the expensive part,
 * which is the more interesting answer and the one this chapter gets.
 */
uint64_t o_lower_bound_ns(uint64_t instructions, uint64_t ipc_x100, uint64_t mhz) {
  (void)instructions;
  (void)ipc_x100;
  (void)mhz;
  return 0; /* Problem 19.2 */
}

/* -- Problem 19.3 -------------------------------------------------------------------------- */
/* Which kind of fault is this, from four facts about the address?
 *
 *   requested   the address lies inside a mapping the process asked for
 *   mapped      the page table translates it right now, with no help from the kernel
 *   resident    a physical page already holds the data this address needs
 *   zero_fill   the page has never been written and the kernel owes only zeroes
 *
 * Return:
 *   O_NONE    no fault at all
 *   O_MINOR   a fault the kernel can satisfy without touching storage
 *   O_MAJOR   a fault that has to wait for storage
 *   O_FATAL   the process never asked for this address
 *
 * The distinction that matters is minor against major, and it is not a distinction about the
 * fault: both enter the kernel by chapter 6's path, and both leave it the same way. What
 * separates them is whether the answer was already in memory, and that is worth three or four
 * orders of magnitude.
 */
#define O_NONE 0
#define O_MINOR 1
#define O_MAJOR 2
#define O_FATAL 3

int o_fault_kind(int requested, int mapped, int resident, int zero_fill) {
  (void)requested;
  (void)mapped;
  (void)resident;
  (void)zero_fill;
  return O_FATAL; /* Problem 19.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

/* Answers are keyed by position rather than by the text of the argument, so that a case whose
 * arguments happen to be empty or to repeat still lands somewhere the caller can find it. */

static void fields(const char *s, uint64_t *v, int n) {
  char *p = (char *)s;
  for (int k = 0; k < n; k++) {
    v[k] = strtoull(p, &p, 10);
    if (*p == ',')
      p++;
  }
}

/* Reads digit `k` of a flag string, treating anything shorter than four digits as zeroes. */
static int flag(const char *s, int k) {
  for (int i = 0; i < k; i++)
    if (s[i] == '\0')
      return 0;
  return s[k] == '1';
}

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    uint64_t v[4] = {0, 0, 0, 0};
    const char *arg = argv[i] + 1;
    switch (argv[i][0]) {
    case 'r': /* r<call>,<clock>,<iterations>,<inside> */
      fields(arg, v, 4);
      printf("reported %d %llu\n", i - 1,
             (unsigned long long)o_reported_ns(v[0], v[1], v[2], (int)v[3]));
      break;
    case 'b': /* b<instructions>,<ipc_x100>,<mhz> */
      fields(arg, v, 3);
      printf("bound %d %llu\n", i - 1, (unsigned long long)o_lower_bound_ns(v[0], v[1], v[2]));
      break;
    case 'f': /* f<requested><mapped><resident><zero_fill> */
      printf("fault %d %d\n", i - 1,
             o_fault_kind(flag(arg, 0), flag(arg, 1), flag(arg, 2), flag(arg, 3)));
      break;
    default:
      fprintf(stderr, "oscost: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end oscost\n");
  return 0;
}
