/* Problems 10.1, 10.2 and 10.3 — build one, reason about one, and find the one that deadlocks.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * None of these is in the repository. `sysfs/lib/ordering.c` shows what five kinds of increment
 * compile to and contains no lock; the kernel's own spinlock is xv6's, is discussed in chapter 10,
 * and is deliberately not the shape you are asked for here.
 *
 *   python3 -m pytest tests/locks_and_memory_ordering
 */

#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -- Problem 10.1 -------------------------------------------------------------------------- */
/* A lock, from an atomic operation and an ordering promise.
 *
 * `locking_acquire` must not return until no other thread is inside. `locking_release` must let
 * exactly one waiter in. You have the whole of <stdatomic.h>; you do not have pthread_mutex, and
 * using it is not the exercise.
 *
 * Two things to get right, and only the first is about mutual exclusion:
 *
 *   - taking the lock must be one indivisible operation, because a read followed by a write is
 *     two things and something can happen in between — chapter 10 prints what that looks like;
 *   - the ordering must be such that work done inside the critical section is visible to the next
 *     thread in. A correct exchange with the wrong memory order is a lock that protects nothing
 *     on a weakly ordered machine, and passes every test on a strongly ordered one.
 *
 * The test hammers this from several threads and counts. A lock that is merely usually right
 * fails, which is the only useful standard for a lock.
 */
struct locking_lock {
  atomic_int state;
};

void locking_init(struct locking_lock *lock) { atomic_store(&lock->state, 0); }

void locking_acquire(struct locking_lock *lock) {
  (void)lock; /* Problem 10.1 */
}

void locking_release(struct locking_lock *lock) {
  (void)lock; /* Problem 10.1 */
}

/* -- Problem 10.2 -------------------------------------------------------------------------- */
/* Is this reordering allowed?
 *
 * Two memory operations appear in this order in the program, with a barrier of some kind between
 * them. Return 1 if the machine is permitted to make them visible to another core in the opposite
 * order, and 0 if it is not.
 *
 * `first` and `second` are 'r' for a read or 'w' for a write, and `same` is 1 if the two touch
 * the same location. Start with that one: a machine may reorder a great many things, and two
 * accesses to the same address are never among them. Program order is always respected per
 * location, which is why single-threaded code works at all and why a race needs two addresses
 * before it needs a barrier.
 *
 * `barrier` says what ordering is present, and which operation carries it:
 *
 *   'n'  nothing at all
 *   'f'  a full fence between them
 *   'a'  the FIRST operation carries acquire ordering
 *   'A'  the SECOND operation carries acquire ordering
 *   'l'  the SECOND operation carries release ordering
 *   'L'  the FIRST operation carries release ordering
 *
 * Four of those six are the point. Acquire and release are one-way, and which way round they are
 * is what people get wrong: an acquire stops later work moving earlier, and does nothing about
 * earlier work moving later; a release stops earlier work moving later, and does nothing about
 * later work moving earlier. So the same annotation on the other operation of the pair buys you
 * nothing at all — and a lock needs one of each, at opposite ends, for exactly that reason.
 */
int locking_may_reorder(char first, char second, char barrier, int same) {
  (void)first;
  (void)second;
  (void)barrier;
  (void)same;
  return 1; /* Problem 10.2 */
}

/* -- Problem 10.3 -------------------------------------------------------------------------- */
/* Do these two code paths disagree about the order locks are taken in?
 *
 * Each path is a string naming the locks it takes, in order, and holds until it is done: "AB"
 * takes A and then B. Return 1 if there is a pair of locks the two paths take in opposite orders,
 * and 0 if there is not.
 *
 * That is the question a lock-ordering rule actually asks, and it is deliberately not "will this
 * particular schedule hang". A conflicting pair is forbidden whether or not you can construct a
 * schedule that hangs today, because the schedule that hangs tomorrow is not yours to choose.
 *
 * Note what it is not about: which locks are taken, or how many. Two paths can use every lock in
 * the system and be perfectly safe, and two paths can share exactly two locks and not be.
 */
int locking_order_conflicts(const char *first_path, const char *second_path) {
  (void)first_path;
  (void)second_path;
  return 0; /* Problem 10.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

#define THREADS 4
#define PER_THREAD 200000

static struct locking_lock the_lock;

/* volatile so that the compiler emits the load, the add and the store rather than proving to
 * itself that it can do the whole loop in a register. That sequence is what chapter 10 is about,
 * and a critical section optimised out of existence protects nothing and proves nothing. */
static volatile long guarded;

static void *hammer(void *unused) {
  (void)unused;
  for (int i = 0; i < PER_THREAD; i++) {
    locking_acquire(&the_lock);
    guarded++; /* deliberately not atomic: the lock is what makes it safe */
    locking_release(&the_lock);
  }
  return NULL;
}

static int hammer_it(void) {
  pthread_t threads[THREADS];

  locking_init(&the_lock);
  guarded = 0;
  for (int i = 0; i < THREADS; i++)
    if (pthread_create(&threads[i], NULL, hammer, NULL) != 0)
      return 1;
  for (int i = 0; i < THREADS; i++)
    pthread_join(threads[i], NULL);
  printf("hammer %d %ld\n", THREADS * PER_THREAD, guarded);
  return 0;
}

int main(int argc, char **argv) {
  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    switch (argv[i][0]) {
    case 'h':
      if (hammer_it() != 0)
        return 1;
      break;
    case 'r': /* r<first><second><barrier><same> */
      printf("reorder %c%c%c%c %d\n", argv[i][1], argv[i][2], argv[i][3], argv[i][4],
             locking_may_reorder(argv[i][1], argv[i][2], argv[i][3], argv[i][4] == '1'));
      break;
    case 'd': /* d<path>,<path> */
      if (comma == NULL) {
        fprintf(stderr, "locking: expected two paths\n");
        return 2;
      }
      *comma = '\0';
      printf("conflict %s %s %d\n", argv[i] + 1, comma + 1,
             locking_order_conflicts(argv[i] + 1, comma + 1));
      break;
    default:
      fprintf(stderr, "locking: unknown command %s\n", argv[i]);
      return 2;
    }
  }
  printf("end locking\n");
  return 0;
}
