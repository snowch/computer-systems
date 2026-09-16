/* Problems 8.1, 8.2 and 8.3 — the three decisions a fault handler is really making.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository. `sysfs/lib/sv39.c` counts page-table pages from addresses
 * and knows nothing about policy; the kernel patch for this chapter counts and decides nothing.
 * The page-faults chapter has everything you need, and the second one is the only place it is spelled out.
 *
 *   python3 -m pytest tests/page_faults_as_a_feature
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PAGE_SIZE 4096

/* One run of bytes a program touches. Bytes, not pages, deliberately: a program does not know
 * where the page boundaries are and neither does its author. */
struct touch {
  uint64_t start;
  uint64_t length;
};

/* -- Problem 8.1 -------------------------------------------------------------------------- */
/* How many first-touch faults will these accesses cause?
 *
 * A page is the unit of everything here, so the answer is the number of distinct pages the runs
 * between them reach — not the number of runs, and not the number of bytes. Two accesses in one
 * page cost one fault; an access of two bytes can cost two, if it lands in the wrong place.
 *
 * Assume nothing is mapped to begin with and that every page is freshly lazy. Runs may overlap,
 * may repeat, and are in no particular order. A run of zero length touches nothing.
 */
uint64_t policy_faults_for(const struct touch *runs, uint64_t count) {
  (void)runs;
  (void)count;
  return 0; /* Problem 8.1 */
}

/* -- Problem 8.2 -------------------------------------------------------------------------- */
/* What should the handler do about this fault?
 *
 * `cause` is what the hardware reported: 13 for a load, 15 for a store, 12 for an instruction
 * fetch. `va` is the address that faulted. `sz` is the process's size — the first address it has
 * never asked for. `mapped` says whether that page already has a valid entry in the page table.
 *
 * That last one is the test it is easiest to leave out and worst to get wrong. A fault on a page
 * that is already mapped is not a page that has never been touched; it is a permission being
 * refused, and a handler that allocates a fresh page for it has just thrown away the contents of
 * a page the program was using.
 *
 * Return one of the three below. The third is not reachable from a correct kernel, which is what
 * makes it worth returning: a handler that is willing to decide anything about an input it should
 * never have received is a handler that hides the bug that sent it.
 */
#define POLICY_ALLOCATE 0 /* a page the process asked for and has not touched */
#define POLICY_KILL 1     /* the process went somewhere it never requested */
#define POLICY_PANIC 2    /* not a page fault at all: this handler should never have been called */

int policy_action(int cause, uint64_t va, uint64_t sz, int mapped) {
  (void)cause;
  (void)va;
  (void)sz;
  (void)mapped;
  return POLICY_KILL; /* Problem 8.2 */
}

/* -- Problem 8.3 -------------------------------------------------------------------------- */
/* When does a program that asks for too much find out?
 *
 * This is what laziness actually costs, and it is not faults. An eager request that cannot be
 * satisfied fails at the call, where the program can check the return value and do something
 * sensible. A lazy request always succeeds, and the shortage is discovered later, by a store
 * instruction — at which point there is no return value to check and nothing to do but kill the
 * process.
 *
 * `policy` is 1 for eager and 2 for lazy, matching the kernel's own constants. `requested` and
 * `available` are in pages; `touched` is how many of the requested pages the program goes on to
 * touch. Return where the failure becomes visible, or that it never does.
 */
#define POLICY_AT_REQUEST 0 /* sbrk returns -1 and the program can handle it */
#define POLICY_AT_TOUCH 1   /* the allocation succeeded and an ordinary store kills the process */
#define POLICY_NEVER 2      /* there was enough, or the program never went looking */

int policy_failure_observed(int policy, uint64_t requested, uint64_t touched, uint64_t available) {
  (void)policy;
  (void)requested;
  (void)touched;
  (void)available;
  return POLICY_NEVER; /* Problem 8.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  struct touch runs[64];
  uint64_t count = 0;

  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    char *second = comma ? strchr(comma + 1, ',') : NULL;
    uint64_t a = strtoull(argv[i] + 1, NULL, 0);
    uint64_t b = comma ? strtoull(comma + 1, NULL, 0) : 0;
    uint64_t c = second ? strtoull(second + 1, NULL, 0) : 0;
    char *third = second ? strchr(second + 1, ',') : NULL;
    uint64_t d = third ? strtoull(third + 1, NULL, 0) : 0;

    switch (argv[i][0]) {
    case 't': /* t<start>,<length> — remember a run */
      if (count < 64) {
        runs[count].start = a;
        runs[count].length = b;
        count++;
      }
      break;
    case 'n': /* n — how many faults do the remembered runs cause? */
      printf("faults %llu\n", (unsigned long long)policy_faults_for(runs, count));
      count = 0;
      break;
    case 'a': /* a<cause>,<va>,<sz>,<mapped> */
      printf("action %llu %llu %llu %d\n", (unsigned long long)a, (unsigned long long)b,
             (unsigned long long)d, policy_action((int)a, b, c, (int)d));
      break;
    case 'o': /* o<policy>,<requested>,<touched>,<available> */
      printf("observed %llu %llu %llu %llu %d\n", (unsigned long long)a, (unsigned long long)b,
             (unsigned long long)c, (unsigned long long)d,
             policy_failure_observed((int)a, b, c, d));
      break;
    default:
      fprintf(stderr, "policy: unknown command %s\n", argv[i]);
      return 2;
    }
  }

  printf("end policy\n");
  return 0;
}
