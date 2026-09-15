"""Problem 3 of ch09 — what a lazy fork would cost instead.

Do not implement copy-on-write. Instead find out, from the machine, what it would have to handle:
map a page without permission to write to it, write to it anyway, and catch the trap.

That trap is the one a copy-on-write fork lives on, and its cause is the answer to half this
problem. The other half is which bit of the page-table entry you had to clear to produce it.

Put your program in `answer_lazy.c` beside this file. It must print

    fork write_fault_cause <n>
    fork page_was_readable 1
    end fork
"""

from __future__ import annotations

#: Which page-table entry bit you cleared, by the letter the specification gives it: R, W, X or U.
THE_BIT_YOU_CLEARED: str = ""

#: Which of ch09's steps copy-on-write would remove, in one sentence.
WHAT_IT_WOULD_REMOVE: str = ""
