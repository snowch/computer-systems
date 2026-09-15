"""Problem 13.2 — which configuration would test this claim?

Also derived from the table. Some claims cannot be tested from some starting points with the six
configurations available, and returning "you cannot" is the right answer rather than a failure.
"""

from __future__ import annotations

import pytest

from tests.ch20.harness import CONFIGS, ask

VARIABLES = "eki"


def expected(claim: str, start: str):
    index = VARIABLES.index(claim)
    for name in sorted(CONFIGS):
        if name == start:
            continue
        a, b = CONFIGS[start], CONFIGS[name]
        differing = [v for v, x, y in zip(VARIABLES, a, b, strict=True) if x != y]
        if differing == [claim]:
            return 1, name
    assert index >= 0
    return 0, "-"


CASES = [(claim, start) for claim in VARIABLES for start in sorted(CONFIGS)]


def test_some_claims_cannot_be_tested_from_where_you_are():
    """Scaffolding: the problem must have both kinds of answer or it is a lookup."""
    verdicts = {expected(claim, start)[0] for claim, start in CASES}
    assert verdicts == {0, 1}, "every claim being testable would make the problem pointless"


@pytest.mark.problem
def test_the_pair_named_isolates_exactly_the_claim(crossing):
    answered = ask(crossing, [f"p{claim}{start}" for claim, start in CASES])
    wrong = {
        f"claim {claim!r} from {start}": {
            "expected": expected(claim, start),
            "got": answered["pair"][f"{claim}{start}"],
        }
        for claim, start in CASES
        if answered["pair"][f"{claim}{start}"] != expected(claim, start)
    }
    assert not wrong, (
        "the configuration named has to differ from the starting one in the claimed variable and "
        f"in nothing else: {wrong}"
    )
