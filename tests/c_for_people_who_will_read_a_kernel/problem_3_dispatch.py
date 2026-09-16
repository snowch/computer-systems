"""Problem 3 of the kernel-C chapter — build the table.

A kernel that must do something different for each of several devices does not write a `switch`.
It writes a table of function pointers and indexes it, which is the pattern the kernel-C chapter's figure
draws and the one [the drivers chapter](#interrupts-and-drivers) uses for real.

Write the table. `OPERATIONS` maps each operation name to the C expression that belongs in that
slot, and the test builds a dispatch table from it, calls through it, and checks the answers.

The functions already exist in `tests/c_for_people_who_will_read_a_kernel/devices.c`. What does not exist is the table, and
getting the *type* of it right is most of the exercise — a table of function pointers has a
declaration that reads badly the first several times.
"""

from __future__ import annotations

#: The operations, in the order the table indexes them.
ORDER = ("reset", "read", "write", "status")

#: Your table: operation name -> the name of the C function that implements it.
#:
#: Every function is declared in tests/c_for_people_who_will_read_a_kernel/devices.c. Three of the four are easy to place and
#: one of them is not what its name suggests, so read them rather than matching strings.
TABLE: dict[str, str] = {}
