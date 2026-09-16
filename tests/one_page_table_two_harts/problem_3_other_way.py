"""Problem 3 of the page-table chapter — lose an update the other way round.

The page-table chapter's program loses the second hart's increment: hart 0 reads, hart 1 does its whole increment
in the gap, hart 0 writes over it. Rearrange the handshake so hart *0* is the one whose work
disappears instead, without changing what the counter ends up holding.

Swapping the two harts' code wholesale does not count, and the test checks for it.

Put your program in `answer_other.c` beside this file. It must print

    harts counter_after 1
    harts updates_lost 1
    harts lost_from_hart <n>
    end harts
"""

from __future__ import annotations

#: Which of the three instructions of a read-modify-write had to move. One of: "load", "add",
#: "store".
WHICH_INSTRUCTION_MOVED: str = ""
