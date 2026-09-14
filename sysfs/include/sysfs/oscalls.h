/* The same request, written twice: once as the instruction and once as the call.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * Chapter 6 showed what a system call is on the inside, by stopping the kernel in the middle of
 * one. This header exists so chapter 19 can show what it is on the *outside*, on a machine whose
 * kernel cannot be stopped — and the answer, once the compiler has had it, is a branch.
 *
 * Neither function is here to be fast. They are here to be disassembled.
 */

#ifndef SYSFS_OSCALLS_H
#define SYSFS_OSCALLS_H

/* Ask the kernel for this process's identifier by executing the trapping instruction directly:
 * put the call number where the calling convention for system calls says it goes, trap, and read
 * the answer out of the register the kernel left it in.
 *
 * The convention is the kernel's, not the C compiler's, and the two are different documents.
 * That is worth meeting once, because it is why a system call cannot simply be a function: the
 * caller and the kernel do not share a toolchain, so they cannot have agreed by being compiled
 * together. */
long sysfs_raw_getpid(void);

/* The same request, written the way anyone would write it. */
long sysfs_libc_getpid(void);

#endif /* SYSFS_OSCALLS_H */
