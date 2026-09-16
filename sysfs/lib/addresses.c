/* The pairs the kernel-C chapter compiles and compares.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Each pair differs by one word, and the machine code differs by much more or not at all. Which
 * of those two it is, is the chapter.
 */

#include "sysfs/addresses.h"

#define READS 4

int sysfs_read_four(const int *slot) {
  int total = 0;
  for (int index = 0; index < READS; index++) {
    total += *slot;
  }
  return total;
}

int sysfs_read_four_volatile(const volatile int *slot) {
  int total = 0;
  for (int index = 0; index < READS; index++) {
    total += *slot;
  }
  return total;
}

/* `const int values[4]` looks like it promises four. It does not: an array parameter is a
 * pointer, the 4 is discarded, and sizeof inside this function measures a pointer. The proof is
 * that this and the function below it compile to the same instructions. */
int sysfs_sum_array(const int values[4]) {
  int total = 0;
  for (int index = 0; index < READS; index++) {
    total += values[index];
  }
  return total;
}

int sysfs_sum_pointer(const int *values) {
  int total = 0;
  for (int index = 0; index < READS; index++) {
    total += values[index];
  }
  return total;
}

/* Nothing outside this file can refer to this, which is what `static` means here. The compiler
 * therefore knows every call site, and is free to do what it likes with it. */
static int add_one(int value) { return value + 1; }

int sysfs_call_by_name(int value) { return add_one(value) * 2; }

int sysfs_uses_private(int value) { return add_one(value) * 2; }

int sysfs_call_through(int (*operation)(int), int value) { return operation(value) * 2; }
