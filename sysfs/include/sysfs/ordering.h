/* What a race is, and what an atomic operation is, at the level where the difference is visible.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The locks chapter's claim is that "two threads updating a counter can lose an update" is not a fact about
 * threads. It is a fact about what `counter++` compiles to, and the only way to be sure of it is
 * to look. These four functions do the same arithmetic under four different promises, and the
 * chapter prints what each becomes.
 */

#ifndef SYSFS_ORDERING_H
#define SYSFS_ORDERING_H

/* An ordinary increment. Whatever this compiles to is what a race is. */
void sysfs_bump_plain(long *counter);

/* The same arithmetic, as one indivisible operation, with no ordering promised about anything
 * else. Enough to make a counter correct and not enough to make a lock. */
void sysfs_bump_relaxed(long *counter);

/* The same again, ordered against every other access in both directions. The difference from
 * the relaxed version is the price of the ordering rather than of the atomicity. */
void sysfs_bump_ordered(long *counter);

/* Publishing a value and then announcing it. The store to `flag` must not become visible before
 * the store to `value`, or a reader that sees the flag may not see the value — which is the
 * whole of what release ordering is for, and is exactly what a lock's release does. */
void sysfs_publish(long *value, int *flag, long payload);

/* The same publication written without any ordering at all, for comparison. It is not a slower
 * version of the one above; it is a different program, and on a weakly ordered machine it is a
 * broken one. */
void sysfs_publish_unordered(long *value, int *flag, long payload);

#endif /* SYSFS_ORDERING_H */
