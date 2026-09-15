/* Problems 7.1, 7.2 and 7.3 — build and follow a real page table.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * `sysfs/lib/sv39.c` splits an address and counts what a set of mappings would cost. It does not
 * walk a page table and it does not build one, so it will not hand you any of the three answers
 * below. Chapter 7 has the shape; the privileged specification @riscv-priv has the entry format.
 *
 *   python3 -m pytest tests/ch09
 *
 * The memory model, so that nothing here needs a kernel. Pages come from an arena, and a
 * "physical address" is a byte offset into it — which is exactly what a physical address is to
 * the hardware, a number it uses to find memory. Two helpers are given because the exercise is
 * page tables and not allocators.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PAGE_SIZE 4096
#define ENTRIES 512
#define ARENA_PAGES 4096

#define PTE_V (1UL << 0)
#define PTE_R (1UL << 1)
#define PTE_W (1UL << 2)
#define PTE_X (1UL << 3)
#define PTE_U (1UL << 4)

/* The two conversions RISC-V defines. A PTE holds a physical page number in bits 53:10, which is
 * why these shift by different amounts: ten out, twelve back. Getting this pair the wrong way
 * round produces a page table that looks plausible and translates nothing. */
#define PA2PTE(pa) ((((uint64_t)(pa)) >> 12) << 10)
#define PTE2PA(pte) ((((uint64_t)(pte)) >> 10) << 12)

static unsigned char arena[ARENA_PAGES * PAGE_SIZE];
static uint64_t arena_used = PAGE_SIZE; /* offset 0 is reserved so that 0 can mean "none" */
static uint64_t arena_handed_out;

/* Given: a zeroed page from the arena, as a physical address. Returns 0 when the arena is full. */
uint64_t walk_alloc(void) {
  if (arena_used + PAGE_SIZE > sizeof(arena))
    return 0;
  uint64_t pa = arena_used;
  arena_used += PAGE_SIZE;
  arena_handed_out++;
  memset(arena + pa, 0, PAGE_SIZE);
  return pa;
}

/* Given: the page at a physical address, as 512 entries you can read and write. */
uint64_t *walk_page(uint64_t pa) { return (uint64_t *)(void *)(arena + pa); }

/* -- Problem 7.1 -------------------------------------------------------------------------- */
/* Map one page: after this, translating `va` must yield `pa`.
 *
 * Allocate the interior tables you need with walk_alloc(), and no more than you need. The test
 * grades this by counting how many pages you took and comparing that with what chapter 7's own
 * model derives from the addresses — so a mapper that allocates eagerly fails even if every
 * mapping it makes is correct. That is the chapter's claim turned into a check: the cost of an
 * address space follows from where its pages are.
 *
 * Return 0 on success and -1 if the arena runs out. `perms` is the R/W/X/U bits for the leaf;
 * you supply V.
 */
int walk_map(uint64_t *root, uint64_t va, uint64_t pa, uint64_t perms) {
  (void)root;
  (void)va;
  (void)pa;
  (void)perms;
  return -1; /* Problem 7.1 */
}

/* -- Problem 7.2 -------------------------------------------------------------------------- */
/* Translate a virtual address, the way the hardware does.
 *
 * Start at `root`, use nine bits of `va` at each level, and follow valid entries down. On success
 * write the physical address — including the offset, which translation never changes — to
 * `*pa_out` and return 0. When the walk cannot continue, return -1 and write nothing.
 *
 * A PTE with V clear is not a mapping. A PTE with V set and none of R, W or X is a pointer to the
 * next level down. A PTE with V set and any of them is a leaf, and the level it was found at
 * decides how much memory it covers — which is worth handling even though 7.1 never makes one.
 *
 * Graded against the mappings your own 7.1 made, so get that one working first.
 */
int walk_translate(const uint64_t *root, uint64_t va, uint64_t *pa_out) {
  (void)root;
  (void)va;
  (void)pa_out;
  return -1; /* Problem 7.2 */
}

/* -- Problem 7.3 -------------------------------------------------------------------------- */
/* Where does the walk first fail?
 *
 * This is what a page fault is: not "the address is wrong" but "the walk stopped, here". Return
 * the level whose table lacked a valid entry — 2, 1 or 0 — or -1 if `va` is mapped.
 *
 * The distinction is the useful one in practice. Failing at level 2 means nothing in that
 * gigabyte of the address space exists at all; failing at level 0 means the neighbourhood is
 * mapped and this page is not, which is a very different bug with a very different cause.
 */
int walk_first_missing_level(const uint64_t *root, uint64_t va) {
  (void)root;
  (void)va;
  return 2; /* Problem 7.3 */
}

/* -- the harness, which you do not need to change ----------------------------------------- */

int main(int argc, char **argv) {
  uint64_t root_pa = walk_alloc();
  uint64_t *root = walk_page(root_pa);

  for (int i = 1; i < argc; i++) {
    char *comma = strchr(argv[i], ',');
    uint64_t first = strtoull(argv[i] + 1, NULL, 0);
    uint64_t second = comma ? strtoull(comma + 1, NULL, 0) : 0;
    uint64_t pa = 0;

    switch (argv[i][0]) {
    case 'm': /* m<va>,<pa> */
      printf("map %#llx %d\n", (unsigned long long)first,
             walk_map(root, first, second, PTE_R | PTE_W | PTE_U));
      break;
    case 't': /* t<va> */
      if (walk_translate(root, first, &pa) == 0)
        printf("translate %#llx %#llx\n", (unsigned long long)first, (unsigned long long)pa);
      else
        printf("translate %#llx fault\n", (unsigned long long)first);
      break;
    case 'f': /* f<va> */
      printf("missing %#llx %d\n", (unsigned long long)first,
             walk_first_missing_level(root, first));
      break;
    default:
      fprintf(stderr, "walk: unknown command %s\n", argv[i]);
      return 2;
    }
  }

  printf("allocated %llu\n", (unsigned long long)arena_handed_out);
  printf("end walk\n");
  return 0;
}
