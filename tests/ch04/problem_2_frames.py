"""Problem 2 of chapter 4 — which of these needs a stack frame?

Four functions. For each, say whether the compiler gives it a stack frame at `-O2`, and if so
whether it has to save the return address.

The test compiles each one and reads the answer out of the prologue, so you are predicting what a
compiler does rather than reciting a rule. Chapter 4's table shows the same measurement for four
different functions, and the reasoning that explains that table explains this one.
"""

from __future__ import annotations

#: The four functions, exactly as the test will compile them.
FUNCTIONS = {
    "adds_two": "long f(long a, long b) { return a + b; }",
    "calls_something": "long g(long); long f(long a) { return g(a) + 1; }",
    "writes_an_array": "long f(long a) { long v[16]; for (int i=0;i<16;i++) v[i]=a+i; return v[a&15]; }",
    "tail_position": "long g(long); long f(long a) { return g(a); }",
}

#: Your answers: name -> (does it get a frame?, does it save the return address?)
ANSWERS: dict[str, tuple[bool, bool]] = {}
