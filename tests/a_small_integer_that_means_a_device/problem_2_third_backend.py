"""Problem 2 of the device-descriptor chapter — add a third backend.

Add a destination that discards everything written to it and reads back as nothing, and show that
the calling code does not change.

"Does not change" is the claim under test, so make it literally true: the same function, called
three times with three different numbers.

Put your program in `answer_third.c` beside this file. It must print

    descriptors backends 3
    descriptors wrote_to_console <n>
    descriptors wrote_to_memory <n>
    descriptors wrote_to_discard <n>
    descriptors read_from_discard 0
    end descriptors
"""

from __future__ import annotations
