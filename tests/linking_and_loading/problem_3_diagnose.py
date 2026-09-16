"""Problem 3 of the linking chapter — read the error, name the cause.

Four link failures, each given as the message a linker actually printed. For each, say what went
wrong, choosing from the causes below.

This is a diagnostic exercise rather than a knowledge one. Linker errors are terse, they name
symbols rather than files, and they are produced by a program that knows nothing about your
intentions — so reading one is a skill, and it is the skill that turns twenty minutes of confusion
into ten seconds.
"""

from __future__ import annotations

#: The causes to choose from.
CAUSES = (
    "nothing defines it",  # the name was used and no object on the line supplies it
    "two things define it",  # the same name is defined in more than one object
    "defined, but the linker had already passed it",  # an archive listed before what needs it
    "defined, but private to its own file",  # `static`, so no other object may name it
)

#: Your answers: message key -> one of CAUSES.
DIAGNOSES: dict[str, str] = {}
