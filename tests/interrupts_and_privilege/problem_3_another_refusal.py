"""Problem 3 of ch05 — find another refusal.

`csrr t0, mhartid` is one instruction supervisor mode may not execute, and it is refused with
cause 2. Find a second refusal of a *different* kind — not another machine-mode register — and say
what cause it produces.

Write the instruction as text the assembler will accept.
"""

from __future__ import annotations

#: One instruction, assembler syntax, that supervisor mode may not perform.
THE_INSTRUCTION: str = ""

#: The cause code it produces. ch05's table has the one you are not allowed to reuse.
ITS_CAUSE: int = 0

#: In one short phrase: why is this refused, given that the instruction itself is legal?
WHY: str = ""
