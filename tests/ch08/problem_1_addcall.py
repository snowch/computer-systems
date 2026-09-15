"""Problem 1 of chapter 6 — add a system call, end to end.

The kernel counts traps and prints the census on Ctrl-T. That is fine for a person at a console
and no use at all to a program, which cannot press Ctrl-T. Give it a system call.

Add `trapcount()`, returning the number of system calls this kernel has served since it booted —
the same number the census prints next to `system call`. Then write a user program that calls it.

Five files have to agree before this works, and finding all five is the exercise. A system call
is not a function: the number that identifies it, the table that dispatches on the number, the
declaration the user program compiles against, the stub that issues `ecall`, and the kernel
function itself are in five different places, and leaving any one of them out produces a failure
that does not mention the others.

Your work goes in `xv6/patches/` as a patch of your own — chapter 6 explains the mechanism, and
`xv6/patches/08-trap-census.patch` is a worked example of the shape.
"""

from __future__ import annotations

#: The name of the user program you add under `xv6/apps/`. The test boots xv6 and runs it.
PROGRAM: str | None = None

#: What your program must print, so the test can check it without parsing xv6's shell:
#:
#:     trapcount <number>
#:
#: and nothing else. The number has to grow between two calls, which is how the test knows you
#: returned a live count rather than a constant.
