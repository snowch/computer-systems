"""Problem 17.1 — which of these loops still contains a branch?

`sysfs/lib/pipeline.c` has two functions that count how many values exceed a threshold. Both are
written with an `if`. Decide, before compiling anything, whether each still contains a branch the
processor could mispredict — and then be graded against what this book's compiler actually did.

    python3 -m pytest tests/the_cpu/test_problem_1_branchy.py

If you get this wrong, you are in good company: this book's own chapter 17 was written on the
assumption that the first one would, and the measurement said otherwise.
"""

from __future__ import annotations

#: function name -> True if a data-dependent conditional branch survives optimisation.
KEEPS_A_BRANCH: dict[str, bool | None] = {
    "sysfs_count_over": None,
    "sysfs_count_over_calling": None,
}
