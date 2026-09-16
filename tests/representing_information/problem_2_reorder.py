"""Problem 2 of the representation chapter — pack the struct.

These five members are declared in an order that wastes space. Give the order that wastes least.

The test compiles your ordering and compares its `sizeof` against the smallest any ordering of
these members can achieve. It does not tell you what that number is, and there is no arithmetic
to memorise: the representation chapter's section on alignment gives you the two rules the compiler is obeying,
and the answer follows from them.

Keep all five. You may not change a type, and you may not add anything.
"""

from __future__ import annotations

#: The members, as C types. Reorder the names in ORDER; this mapping stays as it is.
MEMBERS = {
    "flag": "char",
    "weight": "double",
    "count": "int",
    "tag": "char",
    "code": "short",
}

#: The order the members are declared in now, and the one you are improving on.
DECLARED = ("flag", "weight", "count", "tag", "code")

#: Your ordering. Same five names, arranged to waste the least.
ORDER: tuple[str, ...] = ()
