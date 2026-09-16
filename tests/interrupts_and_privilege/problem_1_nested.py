"""Problem 1 of the privilege chapter — interrupt an interrupt.

Arrange for the timer to fire while the handler is still running, and make it actually happen.

Predict the default behaviour first — it is not what you would guess from the privilege chapter's program alone,
and the reason is one bit that the processor changes on your behalf when it takes a trap.

Put your program in `answer_nested.c` beside this file. It must print

    privilege handler_entries <n>   with n at least 2
    privilege nested 1              only if a handler entry happened inside another
    end privilege
"""

from __future__ import annotations

#: In one sentence: what stops a second interrupt arriving while the handler runs, by default?
WHAT_STOPS_IT_BY_DEFAULT: str = ""
