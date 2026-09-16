/* Four sums and three branches, for the chapter about what a core does between fetch and finish.
 *
 * Copyright 2026 Chris Snow. Apache-2.0 — see LICENSE-CODE.
 *
 * The four sums add the same numbers with the same number of additions. They differ only in how
 * many accumulators they use, which decides how long the chain of dependent additions is — and
 * therefore how many of them the machine can have in flight at once. Instruction counts cannot
 * see that difference at all, which is the crossing chapter's closing point turned into an experiment.
 *
 * The branch functions all perform the same comparison the same number of times. They differ in
 * how predictable the outcome is, which is not a property of the instruction either.
 */

#ifndef SYSFS_PIPELINE_H
#define SYSFS_PIPELINE_H

/* One accumulator: every addition waits for the one before it. */
long sysfs_sum_chain1(const long *values, long count);

/* Two independent accumulators, combined at the end. Same additions, half the chain. */
long sysfs_sum_chain2(const long *values, long count);

/* Four. */
long sysfs_sum_chain4(const long *values, long count);

/* Eight, which is past the point where more helps on most machines — and finding where that
 * point is, on the machine in front of you, is the measurement. */
long sysfs_sum_chain8(const long *values, long count);

/* Count how many values satisfy a condition. Written as a branch, and worth compiling before
 * assuming it is one: a compiler that can see both sides are cheap will replace the branch with a
 * conditional move or a conditional increment, and there is then nothing left to mispredict.
 * The CPU chapter finds out which happened rather than assuming. */
long sysfs_count_over(const long *values, long count, long threshold);

/* The same count, with something in the taken case that cannot be turned into arithmetic. A call
 * is not if-convertible: the machine cannot speculatively *not* make it, so the branch survives
 * and can be mispredicted. This is what it takes to measure a branch on purpose. */
long sysfs_count_over_calling(const long *values, long count, long threshold);

#endif /* SYSFS_PIPELINE_H */
