"""Problem 2 of ch09 — run out of processes.

ch09's table has room for two and `fork` is called once, so the question of what happens when
there is no room never arises. Make it arise: call `fork` until the table is full, decide what it
should return then, and show the caller handling it.

The machine has to survive. A full table is an ordinary condition, not a fault.

Put your program in `answer_full.c` beside this file. It must print

    fork successful_forks <n>
    fork failed_fork_result <n>
    fork caller_survived 1
    end fork
"""

from __future__ import annotations

#: In one short phrase: why is returning the child id 0 a bad way to report this failure?
WHY_NOT_ZERO: str = ""
