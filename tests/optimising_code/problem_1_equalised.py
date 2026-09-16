"""Problems 16.1 and 16.2 — predict what the compiler did, before looking.

The optimisation chapter compiles five hand-optimisations of one loop at three optimisation levels. Answer these
from the source in `sysfs/lib/loops.c` and from what you know about compilers, and then be graded
against what this book's own compiler actually produced.

    python3 -m pytest tests/optimising_code

Nothing here is checked against an opinion. The key is `bench/results/loops-aarch64.json`, which
CI regenerates on every push — so if a future compiler changes its mind, the answer changes with
it and the test tells you.
"""

from __future__ import annotations

#: Problem 16.1 — at -O2, which of the five compile to the *same* number of instructions?
#:
#: Give the groups: a list of lists, each holding the variant names that came out identical. Every
#: variant appears exactly once, and a variant that matches nothing is a group of one. Order does
#: not matter.
#:
#: Names are the suffixes: "plain", "hoisted", "reduced", "unrolled", "everything".
EQUALISED_AT_O2: list[list[str]] | None = None

#: Problem 16.2 — which single hand-optimisation leaves *more* instructions than writing the loop
#: plainly, at -O2? Name one variant.
#:
#: And: does raising the level to -O3 make that variant better or worse? Answer "better", "worse"
#: or "same".
BACKFIRED: str | None = None
BACKFIRED_AT_O3: str | None = None
