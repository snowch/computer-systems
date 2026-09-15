"""Problem 18.1 — which fields will two cores fight over?

Computed from the layouts the test wrote, so the key is derived. The case that matters is two
fields on one line written by the *same* thread: they share a line and cost nothing, because
sharing is not the fault.
"""

from __future__ import annotations

import itertools

import pytest

from tests.ch25.harness import LINE, ask

LAYOUTS = {
    "two owners, one line": [(0, 0), (8, 1)],
    "two owners, a line apart": [(0, 0), (64, 1)],
    "one owner, one line": [(0, 0), (8, 0)],
    "nobody writes the neighbour": [(0, 0), (8, -1)],
    "three on a line, three owners": [(0, 0), (8, 1), (16, 2)],
    "spread over two lines": [(0, 0), (8, 1), (64, 2), (72, 3)],
}


def expected(fields: list[tuple[int, int]]) -> int:
    return sum(
        1
        for (o1, w1), (o2, w2) in itertools.combinations(fields, 2)
        if w1 >= 0 and w2 >= 0 and w1 != w2 and o1 // LINE == o2 // LINE
    )


def test_sharing_a_line_is_not_by_itself_the_fault():
    """Scaffolding: same-owner and unwritten neighbours must both cost nothing."""
    assert expected(LAYOUTS["one owner, one line"]) == 0
    assert expected(LAYOUTS["nobody writes the neighbour"]) == 0
    assert expected(LAYOUTS["two owners, one line"]) == 1
    assert expected(LAYOUTS["three on a line, three owners"]) == 3


@pytest.mark.problem
def test_only_pairs_on_one_line_with_different_writers_count(sharing):
    names = sorted(LAYOUTS)
    commands = [
        f"p{i}," + ".".join(f"{o}:{w}" for o, w in LAYOUTS[name]) for i, name in enumerate(names)
    ]
    answered = ask(sharing, commands)
    wrong = {
        name: {"expected": expected(LAYOUTS[name]), "got": answered["pairs"][i]}
        for i, name in enumerate(names)
        if answered["pairs"][i] != expected(LAYOUTS[name])
    }
    assert not wrong, (
        "a pair contends when two different threads write it and it lands on one line, and not "
        f"otherwise: {wrong}"
    )
