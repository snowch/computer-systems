/* One program's worth of arithmetic, written twice, so that the toolchain's stages are visible.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * ch01 follows a program from source text to a result and asks which of that journey costs
 * anything at run time. The answer is easiest to see when two pieces of code that a reader would
 * call identical are compiled side by side, so this header defines exactly that: the same sum,
 * with the same loop, differing only in whether the compiler can know where the loop stops.
 *
 * Shared between both targets under the same constraints as probe.h — no includes, nothing from
 * libc, printing left to the caller — because an xv6 user program is built -ffreestanding
 * -nostdlib and has none of it. The function bodies arrive through a macro rather than a library
 * because an xv6 user program is one translation unit: the staging tree turns each file in
 * xv6/apps/ into its own program and there is nowhere to put a second object. The macro is what
 * lets the host build and the kernel build compile the same bytes anyway.
 */

#ifndef SYSFS_STAGES_H
#define SYSFS_STAGES_H

/* The preprocessor's contribution, and the whole of it: by the time the compiler runs, this name
 * is gone and only the number remains. That is worth seeing once — a macro is not a variable, and
 * no stage after cpp knows this was ever called anything. */
#define SYSFS_STAGES_SPAN 64

/* The same sum, twice.
 *
 * `folded` counts to a bound the compiler can read. `counted` counts to one that arrives in a
 * register at run time. Nothing else differs: same loop, same accumulator, same arithmetic, same
 * optimisation level. What the compiler does with them does not resemble that at all, and
 * ch01 reads both listings side by side.
 *
 * Defined through a macro so the xv6 app and the host tool are the same bytes. */
#define SYSFS_STAGES_DEFINE_SUMS                            \
  unsigned long sysfs_sum_folded(void) {                    \
    unsigned long total = 0;                                \
    for (unsigned n = 0; n < SYSFS_STAGES_SPAN; n++)        \
      total += n;                                           \
    return total;                                           \
  }                                                         \
                                                            \
  unsigned long sysfs_sum_counted(unsigned span) {          \
    unsigned long total = 0;                                \
    for (unsigned n = 0; n < span; n++)                     \
      total += n;                                           \
    return total;                                           \
  }

unsigned long sysfs_sum_folded(void);
unsigned long sysfs_sum_counted(unsigned span);

/* What the program says. One line per route, then the verdict, so a test can assert on it
 * without a parser and a reader can see at a glance that the two agree. */
#define SYSFS_STAGES_REPORT(print, world)                                        \
  do {                                                                           \
    unsigned long a = sysfs_sum_folded();                                        \
    unsigned long b = sysfs_sum_counted(SYSFS_STAGES_SPAN);                      \
    print("sameanswer %s\n", world);                                             \
    print("span %d\n", (int)SYSFS_STAGES_SPAN);                                  \
    print("folded %d\n", (int)a);                                                \
    print("counted %d\n", (int)b);                                               \
    print("agree %s\n", a == b ? "yes" : "no");                                  \
    print("end sameanswer\n");                                                   \
  } while (0)

#endif /* SYSFS_STAGES_H */
