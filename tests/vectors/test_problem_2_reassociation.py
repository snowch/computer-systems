"""Problem 21.2 — the same numbers, added in two orders, giving two answers.

Everything here is computed in single precision by the test, one addition at a time, so the key is
derived rather than stored — and the two orders are required to produce exactly the bit patterns
that order produces, not merely to be close.
"""

from __future__ import annotations

import pytest

from tests.vectors.harness import add32, ask, bits

# (lanes, values). Integers only: every one of them is exact in single precision, so any
# difference between the two answers comes from the order and from nothing else.
CASES = {
    "a big number and eight small ones": (4, [16_777_216] + [1] * 8),
    "the same, one lane": (1, [16_777_216] + [1] * 8),
    "the same, eight lanes": (8, [16_777_216] + [1] * 8),
    "small numbers, no rounding anywhere": (4, list(range(1, 17))),
    "a big number last": (4, [1] * 8 + [16_777_216]),
    "two big numbers": (4, [16_777_216, 16_777_216] + [1] * 6),
    "fewer elements than lanes": (8, [16_777_216, 1, 1]),
}


def sequential(values: list[int]) -> float:
    total = 0.0
    for value in values:
        total = add32(total, value)
    return total


def lanewise(values: list[int], lanes: int) -> float:
    accumulators = [0.0] * lanes
    for index, value in enumerate(values):
        accumulators[index % lanes] = add32(accumulators[index % lanes], value)
    total = 0.0
    for accumulator in accumulators:
        total = add32(total, accumulator)
    return total


def test_one_lane_is_the_sequential_sum():
    """Scaffolding: the arrangement has to reduce to the original when the width is one.

    If it did not, the difference between the two answers would be an artefact of how the problem
    is posed rather than a fact about floating point.
    """
    values = CASES["the same, one lane"][1]
    assert bits(lanewise(values, 1)) == bits(sequential(values))


def test_the_two_orders_disagree_on_the_case_that_matters():
    """Scaffolding: without this the problem demonstrates nothing."""
    lanes, values = CASES["a big number and eight small ones"]
    assert bits(lanewise(values, lanes)) != bits(sequential(values)), (
        "the small values are lost one at a time in one order and survive in partials in the other"
    )


def test_they_agree_when_nothing_rounds():
    """Scaffolding: the disagreement is not a property of adding in a different order.

    It is a property of adding in a different order *when the intermediate values round*, which is
    why the compiler's rule cannot be "reassociate when the numbers are nice".
    """
    lanes, values = CASES["small numbers, no rounding anywhere"]
    assert bits(lanewise(values, lanes)) == bits(sequential(values))


@pytest.mark.problem
def test_both_orders_give_exactly_what_that_order_gives(lanes):
    names = sorted(CASES)
    commands = [f"s{CASES[name][0]}:" + ".".join(str(v) for v in CASES[name][1]) for name in names]
    answered = ask(lanes, commands)
    wrong = {}
    for index, name in enumerate(names):
        width, values = CASES[name]
        want = (bits(sequential(values)), bits(lanewise(values, width)))
        if answered["sum"][index] != want:
            wrong[name] = {"expected": want, "got": answered["sum"][index]}
    assert not wrong, (
        "left to right for one, and lanes accumulating independently for the other, as bit "
        f"patterns: {wrong}"
    )
