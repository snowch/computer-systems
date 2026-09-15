"""Problem 16.3 — which of these benchmark loops survives the compiler?

`tests/optimising_code/escapes.c` has five functions doing identical arithmetic and differing only in what
becomes of the result. For each, set `True` if you expect the loop to still be there after
optimisation and `False` if you expect the compiler to have removed it.

    python3 -m pytest tests/optimising_code/test_problem_3_escapes.py

You are graded against the compiler, not against an opinion: the test compiles the file at `-O2`
and counts the instructions in each function. A loop that was removed leaves almost nothing.

Two of these are traps and they are traps in opposite directions.
"""

from __future__ import annotations

#: function name -> True if the loop survives optimisation, False if it is removed.
SURVIVES: dict[str, bool | None] = {
    "escapes_dropped": None,
    "escapes_returned": None,
    "escapes_volatile": None,
    "escapes_stored": None,
    "escapes_conditional": None,
}
