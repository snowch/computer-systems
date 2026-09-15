"""Problem 1 of ch07 — add a call, and an error.

ch07 has one way to fail: an unknown call number. Add a call that can fail for a different reason
— something about its arguments rather than about its identity — and return a result the caller can
tell apart from a valid one.

Choosing the sentinel is the interesting half. Say why yours cannot collide with a real answer.

Put your program in `answer_call.c` beside this file. It must print

    syscall ok_result <n>
    syscall failed_result <n>
    syscall caller_can_tell 1
    end syscall
"""

from __future__ import annotations

#: Why your failure value cannot be confused with a successful result.
WHY_THE_SENTINEL_IS_SAFE: str = ""
