"""Problem 3 of ch07 — where does the frame live?

ch07's stub pushes the frame onto whatever stack the caller was using. Say what goes wrong when
the caller arrives with a stack pointer it does not own, then change the stub so the frame goes on
a stack belonging to the handler instead.

Put your program in `answer_stack.c` beside this file. It must print

    syscall frame_on_callers_stack 0
    syscall result_returned 7
    end syscall

so that the call still works after the change.
"""

from __future__ import annotations

#: In one sentence: what can a caller with a bad stack pointer do to the handler?
WHAT_A_BAD_STACK_POINTER_DOES: str = ""

#: The name of the register RISC-V provides for exactly this — somewhere for machine mode to keep
#: a pointer of its own across a trap.
THE_REGISTER_FOR_THIS: str = ""
