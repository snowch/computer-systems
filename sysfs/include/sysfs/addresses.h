/* The parts of C that are really about addresses, each paired with something that looks the same.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * ch03 asks which of C's constructs the *machine* has heard of. Some are instructions to the
 * compiler and vanish (`static`, an array parameter); one is an instruction to the compiler about
 * what it may not do, and survives into every load (`volatile`); one turns a call into a
 * different instruction entirely (a function pointer). The way to tell them apart is to compile
 * both and look, which is what this file exists for.
 */

#ifndef SYSFS_ADDRESSES_H
#define SYSFS_ADDRESSES_H

/* How many times the same address is read. The bodies are identical. */
int sysfs_read_four(const int *slot);
int sysfs_read_four_volatile(const volatile int *slot);

/* An array parameter and a pointer parameter, given the same work to do. */
int sysfs_sum_array(const int values[4]);
int sysfs_sum_pointer(const int *values);

/* Called by name, and called through a variable. */
int sysfs_call_by_name(int value);
int sysfs_call_through(int (*operation)(int), int value);

/* Uses a helper nothing outside this file can name. */
int sysfs_uses_private(int value);

#endif /* SYSFS_ADDRESSES_H */
