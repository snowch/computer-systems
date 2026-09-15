"""Problem 1 of ch08 — duplicate onto a number in use.

ch08's `dup` overwrites whatever was at the target slot without a word. Decide what *should*
happen when the target is already open, implement it, and justify the choice.

There is more than one defensible answer. Refusing every duplicate is not one of them.

Put your program in `answer_onto.c` beside this file. It must print

    descriptors dup_onto_free <n>
    descriptors dup_onto_open <n>
    descriptors old_file_still_reachable <0 or 1>
    end descriptors
"""

from __future__ import annotations

#: In a sentence: what you decided should happen, and why that is better than the alternative.
YOUR_CHOICE_AND_WHY: str = ""
