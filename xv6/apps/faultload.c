/* faultload — ask for memory two ways, touch a known amount of it, and say exactly what it did.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The page-faults chapter compares xv6's two allocation policies, which this kernel already offers: `sbrk` allocates
 * when you ask and `sbrklazy` allocates when you touch. The comparison is only worth anything if
 * the workload is fixed by construction rather than observed to be steady, which is the lesson
 * the trap census paid for — so every quantity below is a constant this program decided, and it prints them
 * so that `bench/run_faults.py` can refuse to record a census that disagrees.
 *
 * The three phases are chosen to bracket the trade rather than to demonstrate a win.
 */

#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

#define PGSIZE 4096

/* A large request of which almost nothing is used: laziness at its best. */
#define SYSFS_SPARSE_PAGES 64
#define SYSFS_SPARSE_TOUCHED 1

/* A request every page of which is used: laziness at its worst, and the same bill either way. */
#define SYSFS_DENSE_PAGES 16

static void touch(char *base, int pages) {
  for (int i = 0; i < pages; i++)
    base[i * PGSIZE] = 1; /* one byte per page, because a page is the unit of everything here */
}

int main(void) {
  char *sparse_lazy = sbrklazy(SYSFS_SPARSE_PAGES * PGSIZE);
  touch(sparse_lazy, SYSFS_SPARSE_TOUCHED);

  char *dense_lazy = sbrklazy(SYSFS_DENSE_PAGES * PGSIZE);
  touch(dense_lazy, SYSFS_DENSE_PAGES);

  char *eager = sbrk(SYSFS_SPARSE_PAGES * PGSIZE);
  touch(eager, SYSFS_SPARSE_TOUCHED);

  printf("faultload asked_lazy %d touched_lazy %d asked_eager %d\n",
         SYSFS_SPARSE_PAGES + SYSFS_DENSE_PAGES, SYSFS_SPARSE_TOUCHED + SYSFS_DENSE_PAGES,
         SYSFS_SPARSE_PAGES);
  printf("end faultload\n");
  exit(0);
}
