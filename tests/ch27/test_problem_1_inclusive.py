"""Problem 20.1 — a flat profile is not the profile you act on.

The trees here are shaped like the finding they are for: the hottest symbol by exclusive samples
is a leaf called from several places, and no single caller looks expensive until the callers'
shares are added back up.
"""

from __future__ import annotations

import pytest

from tests.ch27.harness import ask, tree_command

# Each entry is (parent index, exclusive samples). Parents always precede their children.
TREES = {
    "a chain": [(-1, 1), (0, 2), (1, 4)],
    "one caller, three callees": [(-1, 0), (0, 10), (0, 20), (0, 30)],
    "the leaf everybody calls": [(-1, 1), (0, 2), (0, 2), (1, 40), (2, 40)],
    "two roots": [(-1, 5), (0, 5), (-1, 90)],
    "a root that does everything itself": [(-1, 100)],
    "a deep spine with the work at the bottom": [(-1, 0), (0, 0), (1, 0), (2, 0), (3, 99)],
}


def expected(nodes: list[tuple[int, int]]) -> list[int]:
    inclusive = [exclusive for _, exclusive in nodes]
    for index in range(len(nodes) - 1, -1, -1):
        parent = nodes[index][0]
        if parent >= 0:
            inclusive[parent] += inclusive[index]
    return inclusive


def test_the_flat_ranking_and_the_inclusive_ranking_disagree():
    """Scaffolding: if they agreed, the problem would be teaching nothing.

    In "the leaf everybody calls" the exclusive winner is a leaf, and the inclusive winner is the
    root — which is the only node in the tree anybody can do anything about.
    """
    nodes = TREES["the leaf everybody calls"]
    flat = [exclusive for _, exclusive in nodes]
    deep = expected(nodes)
    assert flat.index(max(flat)) != deep.index(max(deep))
    assert deep[0] == sum(flat), "a single root's inclusive count is the whole profile"


def test_a_spine_of_zeroes_still_carries_the_work_up():
    """Scaffolding: every node on the path to the work is as expensive as the work."""
    assert expected(TREES["a deep spine with the work at the bottom"]) == [99, 99, 99, 99, 99]


@pytest.mark.problem
def test_inclusive_is_the_node_plus_everything_under_it(profiler):
    names = sorted(TREES)
    answered = ask(profiler, [tree_command(TREES[name]) for name in names])
    wrong = {
        name: {"expected": expected(TREES[name]), "got": answered["inclusive"][i]}
        for i, name in enumerate(names)
        if answered["inclusive"][i] != expected(TREES[name])
    }
    assert not wrong, f"a node's inclusive count is its own samples plus its children's: {wrong}"
