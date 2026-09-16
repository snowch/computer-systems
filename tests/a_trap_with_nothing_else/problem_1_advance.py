"""Problem 1 of the trap chapter — why four, and when is it not?

The trap chapter's handler adds four to `mepc` before returning. Say what that four actually is, and then
give a case in this instruction set where adding four would resume in the wrong place.

The second half is the point. RISC-V is not a fixed-width instruction set in the way the first
half of the chapter makes it look, and the consequence for a trap handler is direct.
"""

from __future__ import annotations

#: In one short phrase: what is the four? Not "four bytes" — what *about* the program is four
#: bytes here, and why is the handler entitled to assume it?
WHAT_THE_FOUR_IS: str = ""

#: An assembly instruction, as text the assembler will accept, for which advancing `mepc` by four
#: would resume in the wrong place. One instruction, no directives.
#:
#: The test assembles it and measures it, so a plausible-sounding answer that happens to be four
#: bytes long does not pass.
AN_INSTRUCTION_THAT_BREAKS_IT: str = ""

#: How many bytes that instruction actually occupies.
ITS_LENGTH_IN_BYTES: int = 0
