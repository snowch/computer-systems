/* Sv39 address translation, arithmetic only: no kernel, no privilege, no hardware.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * ch14 takes the position that translation is a lookup a reader can do by hand, and that the only
 * way to believe that is to do it. Everything here is derivable from two numbers in the privileged
 * specification @riscv-priv — a 4096-byte page and an 8-byte entry — and nothing here needs a
 * machine in supervisor mode to be true.
 *
 * The last function is the interesting one. Given the runs of pages an address space maps, it
 * says how many page-table pages Sv39 requires to describe them, from the addresses alone. The
 * chapter checks that prediction against a kernel's own count of its tables.
 */

#ifndef SYSFS_SV39_H
#define SYSFS_SV39_H

#include <stddef.h>
#include <stdint.h>

/* 4096 bytes to a page, 8 bytes to an entry: 512 entries, which is nine bits of index. Three
 * levels of nine then reach 39 bits, and that is the whole of where the name comes from. */
#define SYSFS_SV39_PAGE_SHIFT 12
#define SYSFS_SV39_INDEX_BITS 9
#define SYSFS_SV39_LEVELS 3
#define SYSFS_SV39_ENTRIES (1u << SYSFS_SV39_INDEX_BITS)
#define SYSFS_SV39_PAGE_BYTES (1u << SYSFS_SV39_PAGE_SHIFT)
#define SYSFS_SV39_ENTRY_BYTES 8

/* One run of consecutive mapped pages. Runs are what decide a page table's size. */
struct sysfs_sv39_run {
  uint64_t start; /* virtual address of the first page, page-aligned */
  uint64_t pages;
};

/* The nine bits a given level of the walk uses. Level 2 is consulted first. */
unsigned sysfs_sv39_index(uint64_t va, int level);

/* The twelve bits translation never looks at, and never changes. */
unsigned sysfs_sv39_offset(uint64_t va);

/* How many bytes one entry at this level covers: 4 KiB, 2 MiB, 1 GiB. */
uint64_t sysfs_sv39_span(int level);

/* Build an address from its parts, which is the inverse of reading one. */
uint64_t sysfs_sv39_compose(unsigned l2, unsigned l1, unsigned l0, unsigned offset);

/* Sv39 addresses are 39 bits sign-extended to 64: bits 63..39 must all copy bit 38. An address
 * that fails this is not "out of range", it is not an address, and the hardware faults. */
int sysfs_sv39_canonical(uint64_t va);

/* How many page-table pages these runs require, by level: out[2] is the root, which is always
 * one. Runs must be sorted by `start` and must not overlap. Returns the total. */
uint64_t sysfs_sv39_tables(const struct sysfs_sv39_run *runs, size_t count, uint64_t out[3]);

#endif /* SYSFS_SV39_H */
