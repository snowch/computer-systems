"""Problem 1 of the page-table chapter — map a page rather than a gigabyte.

The page-table chapter's table has three entries and no second level, because a top-level entry may be a leaf
covering a whole gigabyte. Change the alias so it covers four kilobytes instead, which means
building the two levels the chapter skipped.

Put your program in `answer_page.c` beside this file. It must print

    paging alias_reads_the_same 1
    paging top_entry_is_a_leaf 0
    paging levels_walked <n>
    end paging
"""

from __future__ import annotations

#: In one short phrase: what distinguishes a leaf entry from one that points at another table?
WHAT_MAKES_AN_ENTRY_A_LEAF: str = ""
