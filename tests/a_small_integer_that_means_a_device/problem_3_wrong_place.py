"""Problem 3 of the device-descriptor chapter — put the cursor in the wrong place.

Move the cursor out of the open-file table and into the descriptor table, so each descriptor keeps
its own. Produce a program in which that change is visible in the output.

Then say, in one sentence, which real behaviour this would break.

Put your program in `answer_cursor.c` beside this file. It must print the same fields the device-descriptor chapter's does,
including `descriptors cursor_after_dup_write <n>`.
"""

from __future__ import annotations

#: Which everyday behaviour stops working if two descriptors have independent cursors?
WHAT_BREAKS: str = ""
