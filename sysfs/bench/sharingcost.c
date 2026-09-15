/* sharingcost — what four cores cost each other, on the machine being measured.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   sharingcost sharing <threads> packed|padded
 *   sharingcost atomics <plain|relaxed|ordered> <threads> shared|own
 *
 * Two experiments, and the first is the one with no shared data in it. Each thread increments its
 * own counter; the only thing that differs between `packed` and `padded` is whether those
 * counters land on one cache line. Nothing is shared and nothing races, which is the point.
 *
 * The second contends deliberately: the same atomic operation on a counter every thread is
 * writing, against one each thread has to itself.
 */

#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sysfs/ordering.h"
#include "sysfs/sharing.h"
#include "sysfs/timing.h"

#define ROUNDS 2000000
#define MAX_THREADS 16

struct arena {
  struct sysfs_packed packed;
  struct sysfs_padded padded;
};

/* Line-aligned, and that is load-bearing rather than tidy. A struct of uint64_t is aligned to
 * eight bytes by default, so the "packed" pair can land either side of a line boundary — at which
 * point the experiment's two arrangements are the same arrangement and the chapter measures
 * nothing. Unaligned, this printed packed and padded within noise of each other on a four-core
 * machine; the runner now refuses a run where the counters are not where the layout says. */
static _Alignas(SYSFS_LINE_BYTES) struct arena arena;
static long owned[MAX_THREADS * (SYSFS_LINE_BYTES / sizeof(long))];
static long shared_counter;

struct job {
  int index;
  int packed;
  int shared;
  void (*bump)(long *);
};

/* Each thread takes one of the two counters in whichever layout is under test, alternating, so
 * that with two threads the pair is exactly the pair the layout is about. */
static void *sharing_thread(void *raw) {
  struct job *job = raw;
  uint64_t *slot;
  if (job->packed)
    slot = job->index % 2 ? &arena.packed.b : &arena.packed.a;
  else
    slot = job->index % 2 ? &arena.padded.b : &arena.padded.a;
  for (long i = 0; i < ROUNDS; i++)
    *(volatile uint64_t *)slot += 1;
  return NULL;
}

static void *atomic_thread(void *raw) {
  struct job *job = raw;
  /* One counter per line when unshared, so that "uncontended" means uncontended rather than
   * false-shared — which would measure the previous experiment again. */
  long *slot = job->shared ? &shared_counter
                           : &owned[job->index * (SYSFS_LINE_BYTES / sizeof(long))];
  for (long i = 0; i < ROUNDS; i++)
    job->bump(slot);
  return NULL;
}

static uint64_t run(void *(*body)(void *), struct job *jobs, int threads) {
  pthread_t ids[MAX_THREADS];
  uint64_t before = sysfs_now_ns();
  for (int i = 0; i < threads; i++)
    pthread_create(&ids[i], NULL, body, &jobs[i]);
  for (int i = 0; i < threads; i++)
    pthread_join(ids[i], NULL);
  return sysfs_now_ns() - before;
}

int main(int argc, char **argv) {
  if (argc < 3) {
    fprintf(stderr, "usage: sharingcost sharing <threads> packed|padded\n"
                    "       sharingcost atomics <op> <threads> shared|own\n");
    return 2;
  }
  memset(&arena, 0, sizeof arena);
  memset(owned, 0, sizeof owned);
  shared_counter = 0;

  struct job jobs[MAX_THREADS];
  printf("sharingcost rounds %d\n", ROUNDS);

  if (strcmp(argv[1], "sharing") == 0) {
    int threads = atoi(argv[2]);
    int packed = argc > 3 && strcmp(argv[3], "packed") == 0;
    if (threads < 1 || threads > MAX_THREADS)
      return 2;
    for (int i = 0; i < threads; i++)
      jobs[i] = (struct job){.index = i, .packed = packed};
    uint64_t ns = run(sharing_thread, jobs, threads);
    int shares = packed ? sysfs_same_line((uint64_t)(uintptr_t)&arena.packed.a,
                                          (uint64_t)(uintptr_t)&arena.packed.b)
                        : sysfs_same_line((uint64_t)(uintptr_t)&arena.padded.a,
                                          (uint64_t)(uintptr_t)&arena.padded.b);
    printf("sharing threads %d layout %s total_ns %llu increments %lld same_line %d\n", threads,
           packed ? "packed" : "padded", (unsigned long long)ns, (long long)ROUNDS * threads,
           shares);
  } else if (strcmp(argv[1], "atomics") == 0) {
    if (argc < 5)
      return 2;
    int threads = atoi(argv[3]);
    int shared = strcmp(argv[4], "shared") == 0;
    void (*bump)(long *) = sysfs_bump_plain;
    if (strcmp(argv[2], "relaxed") == 0)
      bump = sysfs_bump_relaxed;
    else if (strcmp(argv[2], "ordered") == 0)
      bump = sysfs_bump_ordered;
    if (threads < 1 || threads > MAX_THREADS)
      return 2;
    for (int i = 0; i < threads; i++)
      jobs[i] = (struct job){.index = i, .shared = shared, .bump = bump};
    uint64_t ns = run(atomic_thread, jobs, threads);
    printf("atomics op %s threads %d where %s total_ns %llu increments %lld\n", argv[2], threads,
           shared ? "shared" : "own", (unsigned long long)ns, (long long)ROUNDS * threads);
  } else {
    return 2;
  }
  printf("end sharingcost\n");
  return 0;
}
