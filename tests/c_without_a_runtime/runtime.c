/* Problems 2.1, 2.2 and 2.3 — a pool, a failure, and a missing qualifier.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository.
 *
 *   python3 -m pytest tests/c_without_a_runtime
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 2.1 --------------------------------------------------------------------------- */
/* Hand out objects with no allocator underneath you.
 *
 * `R_POOL` entries, all of them existing for the whole run, exactly as `proc[NPROC]` does. Write
 * the three operations a kernel needs:
 *
 *   r_pool_reset()      every entry unused
 *   r_pool_alloc()      the index of an unused entry, now marked used, or -1 if there are none
 *   r_pool_free(i)      mark entry `i` unused again
 *
 * `r_pool_alloc` must return the *lowest* unused index, so that a sequence of calls is something
 * a test can predict — a real kernel does not promise this, and scanning from the start is what
 * xv6's `allocproc` does anyway.
 *
 * The case worth getting right is the one an application programmer has never written: what
 * happens when there is no entry left. It is not an exception and it is not a crash. It is a
 * value the caller is expected to look at, and ch02's whole last section is about callers that
 * do not.
 *
 * Freeing an entry that is already free, or an index outside the pool, must change nothing.
 */
#define R_POOL 8

static int r_used[R_POOL];

void r_pool_reset(void) {
  (void)r_used; /* Problem 2.1 */
}

int r_pool_alloc(void) {
  return -1; /* Problem 2.1 */
}

void r_pool_free(int index) {
  (void)index; /* Problem 2.1 */
}

/* -- Problem 2.2 --------------------------------------------------------------------------- */
/* Which of these can fail, and what does it return when it does?
 *
 * Each case describes a kernel function by where its memory comes from and what it hands back:
 *
 *   source: 'p'  a fixed pool, like proc[] — there is a maximum
 *           'f'  a page from the free list — there is a maximum, and it moves
 *           's'  the caller's own stack — it already exists
 *           'g'  a file-scope object that exists for the whole run
 *
 *   returns: 'p' a pointer
 *            'i' an int used as a status, where zero means success
 *            'v' nothing at all
 *
 * Return what the function must give back on the failing path:
 *
 *   R_CANNOT_FAIL   the memory it needs already exists, so there is no failing path
 *   R_NULL          it returns a pointer, so failure is a null one
 *   R_NEGATIVE      it returns a status, so failure is a negative value
 *   R_UNREPORTABLE  it can fail and has no way to say so — a bug in the interface
 *
 * The last of those is the interesting answer, and it is a real thing: a function that can run
 * out of something and returns `void` has no way to tell its caller. In a kernel that is not a
 * style opinion. Nothing is above you to notice.
 */
#define R_CANNOT_FAIL 0
#define R_NULL 1
#define R_NEGATIVE 2
#define R_UNREPORTABLE 3

int r_failure_mode(char source, char returns) {
  (void)source;
  (void)returns;
  return R_CANNOT_FAIL; /* Problem 2.2 */
}

/* -- Problem 2.3 --------------------------------------------------------------------------- */
/* What may the compiler do to this loop?
 *
 * A loop reads one address `reads` times. `qualified` is 1 if the address is declared `volatile`
 * and 0 if it is not. `used` is 1 if the value read is used for something the program's output
 * depends on, and 0 if it is discarded.
 *
 * Return how many reads the compiler is *permitted* to leave in the emitted code — the smallest
 * number a correct compiler could get away with.
 *
 *   volatile          every access in the source must appear in the output, in order
 *   not volatile, and the value is used     the reads are of the same unchanging address, so one
 *                                           suffices
 *   not volatile, and the value is not used it need not read at all
 *
 * `reads` is at least 1. The middle case is the one that turns a driver into a program that
 * receives one character for ever, and *Memory Is One Array* prints the two listings side by side.
 */
uint64_t r_permitted_reads(uint64_t reads, int qualified, int used) {
  (void)reads;
  (void)qualified;
  (void)used;
  return 0; /* Problem 2.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

/* Answers are keyed by the command's position, so two cases with identical arguments still land
 * somewhere the caller can find them. */

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *arg = argv[i] + 1;
    switch (argv[i][0]) {
    case 'p': { /* p<ops> — a script of operations: r reset, a alloc, 0-7 free that index */
      printf("pool %d", i - 1);
      for (char *op = arg; *op; op++) {
        if (*op == 'r')
          r_pool_reset();
        else if (*op == 'a')
          printf(" %d", r_pool_alloc());
        else if (*op >= '0' && *op <= '9')
          r_pool_free(*op - '0');
        else if (*op == 'x')
          r_pool_free(-1);
      }
      printf("\n");
      break;
    }
    case 'f': /* f<source><returns> */
      printf("failure %d %d\n", i - 1, r_failure_mode(arg[0], arg[0] ? arg[1] : 0));
      break;
    case 'v': { /* v<reads>,<qualified>,<used> */
      uint64_t v[3] = {0, 0, 0};
      char *p = arg;
      for (int k = 0; k < 3; k++) {
        v[k] = strtoull(p, &p, 10);
        if (*p == ',')
          p++;
      }
      printf("reads %d %llu\n", i - 1,
             (unsigned long long)r_permitted_reads(v[0], (int)v[1], (int)v[2]));
      break;
    }
    default:
      fprintf(stderr, "runtime: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end runtime\n");
  return 0;
}
