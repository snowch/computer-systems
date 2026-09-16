"""Problem 2 of the trap chapter — make it loop, then explain it.

Take the trap chapter's trap program, remove the line that advances `mepc`, and put the result in
`answer_forever.c` beside this file. It is linked against the same runtime as the chapter's own
programs.

Then say what happens, in terms of instructions rather than symptoms. "It hangs" is a description
of your terminal; the machine is doing something very specific, extremely fast.
"""

from __future__ import annotations

#: The mnemonic of the one instruction that executes over and over. Just the mnemonic.
THE_INSTRUCTION_THAT_REPEATS: str = ""

#: In one sentence: why does the processor not detect this and report an error?
WHY_NO_ERROR: str = ""
