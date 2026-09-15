"""Problem 1 of ch09 — make the child run first.

ch09's parent continues after `fork` and the child waits. Swap it: the child runs to completion
before the parent resumes, and both still report what they reported before.

Put your program in `answer_child_first.c` beside this file. It must print everything ch09's does,
plus

    fork first_to_finish <n>     the process id that finished first
"""

from __future__ import annotations

#: In one sentence: what has to be saved before the parent can be set aside mid-call?
WHAT_HAS_TO_BE_SAVED: str = ""
