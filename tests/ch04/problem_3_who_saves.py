"""Problem 3 of chapter 4 — which register did it not bother to save, and why was that allowed?

A function that calls another function has a problem: the callee may use any register it likes,
so anything this function still needs afterwards has to survive somehow. The calling convention
settles it by dividing the registers in two, and every prologue you will ever read is an
application of that division.

The test compiles a function that both calls out and keeps a value across the call, then asks you
for two registers:

  * one it **writes to and never saves** — it was allowed to, and you should be able to say why;
  * one it **saves before using and restores before returning** — it had to.

Name them by their ABI names (`a0`, `t1`, `s2`, and so on) rather than by number, because the
numbers are the part nobody remembers and the names are the part that means something.

Appendix A lists the two groups. Chapter 4 explains the rule that puts a register in one or the
other, and the rule is short enough that you should not need the list.
"""

from __future__ import annotations

#: A register the function writes without saving first.
USED_FREELY: str | None = None

#: A register the function saves on entry and restores on exit.
SAVED_FIRST: str | None = None
