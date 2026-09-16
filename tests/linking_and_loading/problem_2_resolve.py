"""Problem 2 of the linking chapter — which of these links, and which does not?

Five pairs of translation units. For each, say whether the linker can produce a program.

The test compiles and links each pair for real and reports what happened, so you are predicting a
linker rather than reciting rules about one. Some of these fail for reasons the compiler never
sees, which is the point: a compiler checks one file at a time and a linker is the first thing
that looks at all of them together.
"""

from __future__ import annotations

#: Each case is (first translation unit, second translation unit).
CASES = {
    "declared_and_defined": (
        "int helper(int);\nint main(void){ return helper(1); }",
        "int helper(int x){ return x; }",
    ),
    "declared_never_defined": (
        "int helper(int);\nint main(void){ return helper(1); }",
        "int unrelated(void){ return 0; }",
    ),
    "defined_twice": (
        "int helper(int x){ return x; }\nint main(void){ return helper(1); }",
        "int helper(int x){ return x + 1; }",
    ),
    "static_in_each": (
        "static int helper(int x){ return x; }\nint main(void){ return helper(1); }",
        "static int helper(int x){ return x + 1; }\nint unused(void){ return helper(2); }",
    ),
    "wrong_type_same_name": (
        "double helper(double);\nint main(void){ return (int)helper(1.0); }",
        "int helper(int x){ return x; }",
    ),
}

#: Your answers: case name -> True if the pair links, False if it does not.
LINKS: dict[str, bool] = {}
