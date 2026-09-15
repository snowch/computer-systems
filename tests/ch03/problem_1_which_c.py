"""Problem 1 of chapter 3 — which C produced this?

Four listings, four candidate functions, and the job is to say which is which.

You are not expected to do it by eye, and guessing from the shapes is the slow way. Every
candidate is C you can compile: put each one in a file, build it the way `sysfs/tools/stages.sh`
does, disassemble it and compare. That loop — *change the source, look at the output* — is the
one this chapter is really teaching, and the rest of Part II assumes you have it.
"""

from __future__ import annotations

#: The candidates. Each is a complete function; nothing has been elided.
CANDIDATES = {
    "counted_loop": "int f(int n) { int t = 0; for (int i = 0; i < n; i++) t += i; return t; }",
    "indirect_call": "int f(int (*g)(int), int x) { return g(x); }",
    "volatile_read": "int f(volatile int *p) { return *p + *p; }",
    "plain_read": "int f(const int *p) { return *p + *p; }",
}

#: Your answers: listing name -> candidate name.
ANSWERS: dict[str, str] = {}
