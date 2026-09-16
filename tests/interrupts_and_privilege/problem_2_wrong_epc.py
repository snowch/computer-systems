"""Problem 2 of the privilege chapter — advance `mepc` on an interrupt.

The trap chapter's handler added four to `mepc`, correctly. Make an interrupt handler do the same, and produce
a program in which the damage is *visible in the output* rather than inferred.

The damage is not a crash, which is what makes it worth a problem.

Put your program in `answer_skip.c` beside this file. It must print

    privilege expected <n>
    privilege actual <m>
    end privilege

where the two differ, and where the difference is caused by the advance rather than by counting
something else.
"""

from __future__ import annotations

#: In one sentence: what does the interrupted program lose?
WHAT_GOES_WRONG: str = ""
