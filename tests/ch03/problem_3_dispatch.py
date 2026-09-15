"""Problem 3 of chapter 3 — build the table.

A kernel that must do something different for each of several devices does not write a `switch`.
It writes a table of function pointers and indexes it, which is the pattern chapter 3's figure
draws and the one [ch16](#ch16) uses for real.

Write the table. `OPERATIONS` maps each operation name to the C expression that belongs in that
slot, and the test builds a dispatch table from it, calls through it, and checks the answers.

The functions already exist in `tests/ch03/devices.c`. What does not exist is the table, and
getting the *type* of it right is most of the exercise — a table of function pointers has a
declaration that reads badly the first several times.
"""

from __future__ import annotations

#: The operations, in the order the table indexes them.
ORDER = ("reset", "read", "write", "status")

#: Your table: operation name -> the name of the C function that implements it.
#:
#: Every function is declared in tests/ch03/devices.c. Three of the four are easy to place and
#: one of them is not what its name suggests, so read them rather than matching strings.
TABLE: dict[str, str] = {}
