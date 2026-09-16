/* Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE. */

#include "sysfs/oscalls.h"

#include <unistd.h>

/* `getpid` is call number 172 in the system-call table Linux gives new architectures, which is
 * the table both of this book's architectures use. It is written here as a number rather than
 * taken from a header because the point of this file is to show the trap with nothing in front
 * of it, and `SYS_getpid` would put a header's macro in the way of that. */
#define SYSFS_NR_GETPID 172

long sysfs_raw_getpid(void) {
#if defined(__aarch64__)
  /* x8 carries the call number and x0 comes back with the result. `svc` is the instruction that
   * changes privilege level; everything the kernel then does is the traps-and-system-calls chapter's subject. */
  register long number asm("x8") = SYSFS_NR_GETPID;
  register long result asm("x0");
  asm volatile("svc #0" : "=r"(result) : "r"(number) : "memory");
  return result;
#elif defined(__riscv)
  /* The same three ideas in the instruction set the traps-and-system-calls chapter used: a7 carries the number, a0 comes
   * back with the result, and `ecall` is the instruction xv6's `uservec` is waiting for. */
  register long number asm("a7") = SYSFS_NR_GETPID;
  register long result asm("a0");
  asm volatile("ecall" : "=r"(result) : "r"(number) : "memory");
  return result;
#else
  return getpid();
#endif
}

long sysfs_libc_getpid(void) { return getpid(); }
