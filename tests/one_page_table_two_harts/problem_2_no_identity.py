"""Problem 2 of the page-table chapter — break it on purpose.

Remove one of the two identity mappings. Before running it, predict exactly which cause the
machine reports. Then run it and find out.

Put your program in `answer_broken.c` beside this file. It must survive long enough to print

    paging failure_cause <n>
    end paging

which means the trap has to be caught rather than merely suffered.
"""

from __future__ import annotations

#: The cause code you predict, written down before you run anything.
YOUR_PREDICTION: int = -1
