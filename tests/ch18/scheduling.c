/* Problems 11.1, 11.2 and 11.3 — what a switch must keep, what a sleeper must not miss, and
 * what a policy actually decides.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository.
 *
 *   python3 -m pytest tests/ch18
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 11.1 -------------------------------------------------------------------------- */
/* Must `swtch` save this register?
 *
 * `class` is the register's role under the calling convention of chapter 4: 'a' for an argument
 * or return register, 't' for a temporary, 's' for a saved register, and 'r' for the return
 * address or the stack pointer. `live` is 1 if the switching function still needs the value after
 * the switch returns.
 *
 * Return 1 if the switch itself has to preserve it, and 0 if somebody else already has.
 *
 * The whole of this question is that a context switch is an ordinary function call. Chapter 4's
 * convention already says who keeps what across a call, and a switch inherits that agreement
 * rather than replacing it — which is why it saves less than half of what chapter 6's trap path
 * has to, and why "a switch is expensive" is a claim that needs a number rather than a shrug.
 */
int sched_must_save(char class, int live) {
  (void)class;
  (void)live;
  return 1; /* Problem 11.1 */
}

/* -- Problem 11.2 -------------------------------------------------------------------------- */
/* Does the sleeper wake?
 *
 * `events` is a string describing what happened, in order, from two threads:
 *
 *   'c'  the sleeper checks the condition and finds it false
 *   'L'  the sleeper takes the lock that guards the condition
 *   'U'  the sleeper releases that lock
 *   's'  the sleeper sleeps
 *   'm'  the waker makes the condition true
 *   'w'  the waker wakes anything sleeping
 *
 * Return 1 if the sleeper is still asleep at the end of the sequence with the condition true —
 * that is, if the wakeup was lost — and 0 otherwise.
 *
 * A wakeup aimed at a thread that has not gone to sleep yet hits nothing and is not repeated.
 * That is the entire bug, and the reason a sleeping primitive has to be handed the lock rather
 * than being called after releasing it.
 */
int sched_wakeup_lost(const char *events) {
  (void)events;
  return 0; /* Problem 11.2 */
}

/* -- Problem 11.3 -------------------------------------------------------------------------- */
/* In what order does this policy run them?
 *
 * `bursts` gives how long each of `count` jobs would run if left alone, all of them runnable from
 * the start. `policy` is 'f' for first-come-first-served, 's' for shortest-job-first, or 'r' for
 * round-robin with a quantum of 1.
 *
 * Write into `order` the index of the job that runs in each slot, for `slots` slots, stopping
 * early if every job has finished. Return how many slots you filled.
 *
 * Under 'f' and 's' a job runs to completion once started. Under 'r' every runnable job gets one
 * unit in turn, in index order, until it is done. Ties go to the lower index.
 */
int sched_order(const int *bursts, int count, char policy, int *order, int slots) {
  (void)bursts;
  (void)count;
  (void)policy;
  (void)order;
  (void)slots;
  return 0; /* Problem 11.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  int order[64];

  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    switch (argv[i][0]) {
    case 'v': /* v<class><live> */
      printf("save %c%c %d\n", argv[i][1], argv[i][2],
             sched_must_save(argv[i][1], argv[i][2] == '1'));
      break;
    case 'l': /* l<index>,<events> */
      if (comma == NULL)
        return 2;
      *comma = '\0';
      printf("lost %s %d\n", argv[i] + 1, sched_wakeup_lost(comma + 1));
      break;
    case 'o': { /* o<policy>,<burst>.<burst>... */
      if (comma == NULL)
        return 2;
      int bursts[32], count = 0;
      for (char *p = comma + 1; *p && count < 32;) {
        bursts[count++] = (int)strtol(p, &p, 10);
        if (*p == '.')
          p++;
      }
      int filled = sched_order(bursts, count, argv[i][1], order, 64);
      printf("order %c", argv[i][1]);
      for (int j = 0; j < filled && j < 64; j++)
        printf(" %d", order[j]);
      printf("\n");
      break;
    }
    default:
      fprintf(stderr, "scheduling: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end scheduling\n");
  return 0;
}
