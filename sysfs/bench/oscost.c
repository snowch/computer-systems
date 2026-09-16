/* oscost — what Linux charges for the three services Part IV took apart.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 *   oscost services   a system call, a fault and a switch, each beside a baseline
 *   oscost faults     a minor fault against a major one
 *   oscost vdso       the same request, with and without the privilege change
 *
 * Every figure here is reported beside something, because a duration alone is not a cost. The
 * baselines are chosen to be unflattering: in each pair the difference is doing the thing against
 * not doing it.
 *
 * The raw system call is written here rather than taken from sysfs/lib/oscalls.c on purpose. That
 * file is disassembled by the OS-cost chapter and its listings are committed; adding to it would move them
 * for a reason that has nothing to do with what the chapter shows.
 */

#define _GNU_SOURCE

#include <fcntl.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#include "sysfs/timing.h"

#define ROUNDS 200000
#define PAGES 4096
#define PAGE 4096
#define RUNS 32

static uint64_t samples[RUNS];

/* The trapping instruction with nothing in front of it. 172 is `getpid` and 113 is
 * `clock_gettime` in the system-call table Linux gives new architectures. */
#define NR_GETPID 172
#define NR_CLOCK_GETTIME 113

#if defined(__aarch64__) || defined(__riscv)
#define RAW_ROUTE "raw"
#else
#define RAW_ROUTE "libc"
#endif

static long raw_getpid(void) {
#if defined(__aarch64__)
  register long number asm("x8") = NR_GETPID;
  register long result asm("x0");
  asm volatile("svc #0" : "=r"(result) : "r"(number) : "memory");
  return result;
#elif defined(__riscv)
  register long number asm("a7") = NR_GETPID;
  register long result asm("a0");
  asm volatile("ecall" : "=r"(result) : "r"(number) : "memory");
  return result;
#else
  return getpid();
#endif
}

static long raw_clock_gettime(struct timespec *ts) {
#if defined(__aarch64__)
  register long number asm("x8") = NR_CLOCK_GETTIME;
  register long which asm("x0") = CLOCK_MONOTONIC;
  register long buffer asm("x1") = (long)ts;
  register long result asm("x0");
  asm volatile("svc #0" : "=r"(result) : "r"(number), "r"(which), "r"(buffer) : "memory");
  return result;
#elif defined(__riscv)
  register long number asm("a7") = NR_CLOCK_GETTIME;
  register long which asm("a0") = CLOCK_MONOTONIC;
  register long buffer asm("a1") = (long)ts;
  register long result asm("a0");
  asm volatile("ecall" : "=r"(result) : "r"(number), "r"(which), "r"(buffer) : "memory");
  return result;
#else
  return clock_gettime(CLOCK_MONOTONIC, ts);
#endif
}

/* Something the compiler cannot see through and cannot delete, so that "an empty function call"
 * is a call rather than nothing. */
long sysfs_oscost_nothing(void);
long sysfs_oscost_nothing(void) { return 0; }

static uint64_t best_of(uint64_t (*body)(void)) {
  for (int i = 0; i < RUNS; i++)
    samples[i] = body();
  return sysfs_summarise(samples, RUNS).min;
}

static volatile long sink;

static uint64_t time_raw_getpid(void) {
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < ROUNDS; i++)
    sink = raw_getpid();
  return sysfs_now_ns() - before;
}

static uint64_t time_empty_call(void) {
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < ROUNDS; i++)
    sink = sysfs_oscost_nothing();
  return sysfs_now_ns() - before;
}

/* A fresh anonymous mapping, touched once per page. Every touch is a fault the kernel satisfies
 * without going anywhere, which is what "minor" means. */
static uint64_t time_first_touch(void) {
  char *area = mmap(NULL, (size_t)PAGES * PAGE, PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (area == MAP_FAILED)
    return 0;
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < PAGES; i++)
    area[i * PAGE] = 1;
  uint64_t each = (sysfs_now_ns() - before) / PAGES;
  munmap(area, (size_t)PAGES * PAGE);
  return each;
}

static uint64_t time_second_touch(void) {
  char *area = mmap(NULL, (size_t)PAGES * PAGE, PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (area == MAP_FAILED)
    return 0;
  for (long i = 0; i < PAGES; i++)
    area[i * PAGE] = 1;
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < PAGES; i++)
    area[i * PAGE] = 2;
  uint64_t each = (sysfs_now_ns() - before) / PAGES;
  munmap(area, (size_t)PAGES * PAGE);
  return each;
}

/* A page the kernel has to fetch. The file is written, flushed, and then its cache is dropped
 * with posix_fadvise — which needs no privilege, unlike /proc/sys/vm/drop_caches. */
static uint64_t time_major_fault(const char *path) {
  int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0600);
  if (fd < 0)
    return 0;
  char *block = calloc(PAGE, 1);
  for (long i = 0; i < PAGES; i++)
    if (write(fd, block, PAGE) != PAGE)
      break;
  free(block);
  fsync(fd);
  posix_fadvise(fd, 0, (off_t)PAGES * PAGE, POSIX_FADV_DONTNEED);

  char *area = mmap(NULL, (size_t)PAGES * PAGE, PROT_READ, MAP_PRIVATE, fd, 0);
  if (area == MAP_FAILED) {
    close(fd);
    return 0;
  }
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < PAGES; i++)
    sink += area[i * PAGE];
  uint64_t each = (sysfs_now_ns() - before) / PAGES;
  munmap(area, (size_t)PAGES * PAGE);
  close(fd);
  unlink(path);
  return each;
}

/* A round trip through a pipe between two threads is a switch each way; the same round trip on
 * one thread is the two system calls with no switch in them. The difference is the switch. */
struct pipes {
  int there[2];
  int back[2];
};

static void *pong(void *raw) {
  struct pipes *p = raw;
  char byte;
  for (long i = 0; i < ROUNDS / 100; i++) {
    if (read(p->there[0], &byte, 1) != 1)
      break;
    if (write(p->back[1], &byte, 1) != 1)
      break;
  }
  return NULL;
}

static uint64_t time_switch(void) {
  struct pipes p;
  if (pipe(p.there) || pipe(p.back))
    return 0;
  pthread_t other;
  pthread_create(&other, NULL, pong, &p);
  char byte = 1;
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < ROUNDS / 100; i++) {
    if (write(p.there[1], &byte, 1) != 1)
      break;
    if (read(p.back[0], &byte, 1) != 1)
      break;
  }
  uint64_t each = (sysfs_now_ns() - before) / (ROUNDS / 100) / 2;
  pthread_join(other, NULL);
  close(p.there[0]); close(p.there[1]); close(p.back[0]); close(p.back[1]);
  return each;
}

static uint64_t time_pipe_alone(void) {
  int fds[2];
  if (pipe(fds))
    return 0;
  char byte = 1;
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < ROUNDS / 100; i++) {
    if (write(fds[1], &byte, 1) != 1)
      break;
    if (read(fds[0], &byte, 1) != 1)
      break;
  }
  uint64_t each = (sysfs_now_ns() - before) / (ROUNDS / 100) / 2;
  close(fds[0]); close(fds[1]);
  return each;
}

static uint64_t time_vdso_clock(void) {
  struct timespec ts;
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < ROUNDS; i++) {
    clock_gettime(CLOCK_MONOTONIC, &ts);
    sink += ts.tv_nsec;
  }
  return sysfs_now_ns() - before;
}

static uint64_t time_trapped_clock(void) {
  struct timespec ts;
  uint64_t before = sysfs_now_ns();
  for (long i = 0; i < ROUNDS; i++) {
    raw_clock_gettime(&ts);
    sink += ts.tv_nsec;
  }
  return sysfs_now_ns() - before;
}

int main(int argc, char **argv) {
  const char *what = argc > 1 ? argv[1] : "services";
  printf("oscost rounds %d pages %d raw_route %s\n", ROUNDS, PAGES, RAW_ROUTE);

  if (strcmp(what, "services") == 0) {
    printf("service syscall total_ns %llu baseline_total_ns %llu over %d\n",
           (unsigned long long)best_of(time_raw_getpid),
           (unsigned long long)best_of(time_empty_call), ROUNDS);
    printf("service fault total_ns %llu baseline_total_ns %llu over %d\n",
           (unsigned long long)best_of(time_first_touch),
           (unsigned long long)best_of(time_second_touch), 1);
    printf("service switch total_ns %llu baseline_total_ns %llu over %d\n",
           (unsigned long long)best_of(time_switch),
           (unsigned long long)best_of(time_pipe_alone), 1);
  } else if (strcmp(what, "faults") == 0) {
    printf("fault none ns %llu\n", (unsigned long long)best_of(time_second_touch));
    printf("fault minor ns %llu\n", (unsigned long long)best_of(time_first_touch));
    /* Once only: dropping the cache and reading it back is the measurement, and repeating it
     * would mostly measure a cache that is no longer cold. */
    printf("fault major ns %llu\n", (unsigned long long)time_major_fault("oscost-major.tmp"));
  } else if (strcmp(what, "vdso") == 0) {
    printf("route clock_gettime vdso total_ns %llu over %d\n",
           (unsigned long long)best_of(time_vdso_clock), ROUNDS);
    printf("route clock_gettime trap total_ns %llu over %d\n",
           (unsigned long long)best_of(time_trapped_clock), ROUNDS);
    printf("route getpid trap total_ns %llu over %d\n",
           (unsigned long long)best_of(time_raw_getpid), ROUNDS);
  } else {
    fprintf(stderr, "usage: oscost services|faults|vdso\n");
    return 2;
  }
  printf("end oscost\n");
  return 0;
}
