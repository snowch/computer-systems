"""Problem 2 of ch07 — save one register fewer.

Remove exactly one store and its matching load from the entry stub, and write a program in which
that omission is visible in the output rather than merely possible.

Put your program in `answer_fewer.c` beside this file. It must print

    syscall dropped_register <n>     the x-number you stopped saving
    syscall before <n>
    syscall after <n>
    end syscall

where before and after differ, and differ because of the register you dropped.
"""

from __future__ import annotations

#: The x-number of the register you stopped saving, e.g. 18 for x18.
WHICH_REGISTER: int = -1
