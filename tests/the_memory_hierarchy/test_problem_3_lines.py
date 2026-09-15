"""Problem 15.3 — how many lines does this loop touch?

Computed from the parameters, so the key is derived. The two cases that matter are a stride below
a line, where elements share, and a stride at or above one, where they cannot — and where making
the stride larger stops making anything worse.
"""

from __future__ import annotations

import math

import pytest

from tests.the_memory_hierarchy.harness import ask

LINE = 64

#: (elements, element bytes, stride in elements)
CASES = [
    (64, 8, 1),  # eight per line
    (64, 8, 2),  # four per line
    (64, 8, 8),  # one per line exactly
    (64, 8, 16),  # one per line, and the extra stride buys the machine nothing back
    (64, 8, 64),
    (1, 8, 1),
    (0, 8, 1),
]


def expected(elements: int, element_bytes: int, stride_elements: int) -> int:
    if elements == 0:
        return 0
    span = stride_elements * element_bytes
    per_line = max(1, LINE // span) if span < LINE else 1
    return math.ceil(elements / per_line)


def test_the_count_stops_growing_once_a_stride_reaches_a_line():
    """Scaffolding: the ceiling is the shape that surprises people, so it must be in the cases."""
    assert expected(64, 8, 8) == expected(64, 8, 16) == expected(64, 8, 64) == 64
    assert expected(64, 8, 1) == 8, "eight eight-byte elements share a sixty-four-byte line"


@pytest.mark.problem
def test_the_lines_touched_follow_from_the_stride(hierarchy):
    # One question per run: the harness keys its answers by element count, and several of these
    # cases share one.
    wrong = {}
    for elements, element_bytes, stride in CASES:
        got = ask(hierarchy, [f"t{elements},{element_bytes},{stride},{LINE}"])["lines"][elements]
        if got != expected(elements, element_bytes, stride):
            wrong[f"{elements} elements of {element_bytes} bytes, stride {stride}"] = {
                "expected": expected(elements, element_bytes, stride),
                "got": got,
            }
    assert not wrong, (
        "below a line, elements share it; at or above one, they cannot, and a bigger stride "
        f"cannot make it worse than one line each: {wrong}"
    )
