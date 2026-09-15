"""Problem 17.2 — how long is the critical path?

Computed from the parameters. The number of additions does not change with the accumulator count;
this does, and it is the one the machine's throughput follows.
"""

from __future__ import annotations

import math

import pytest

from tests.ch19.harness import ask

CASES = [(1024, 1), (1024, 2), (1024, 4), (1024, 8), (1024, 1024), (7, 4), (0, 4)]


def expected(elements: int, accumulators: int) -> int:
    if elements == 0:
        return 0
    per = math.ceil(elements / accumulators)
    return per + math.ceil(math.log2(accumulators)) if accumulators > 1 else per


def test_more_accumulators_always_shorten_the_path():
    """Scaffolding, and a limitation of the model worth stating rather than hiding.

    The path keeps shrinking as accumulators are added, all the way to one element each — so this
    model predicts that more is always better, and on a real machine it is not. What stops it is
    not the critical path; it is that accumulators live in registers, there are a fixed number of
    those, and past that point they spill to memory and ch17 takes over. The model is right about
    what it models and silent about what limits it, which is worth knowing about a model.
    """
    lengths = [expected(1024, a) for a in (1, 2, 4, 8, 1024)]
    assert lengths == sorted(lengths, reverse=True), "more accumulators must shorten the path"
    assert expected(1024, 1) > 5 * expected(1024, 8), "and the first few must shorten it a lot"


@pytest.mark.problem
def test_the_path_is_the_share_plus_the_combining_tree(predictor):
    answered = ask(predictor, [f"c{e},{a}" for e, a in CASES])
    wrong = {
        f"{e} elements into {a} accumulators": {
            "expected": expected(e, a),
            "got": answered["path"][f"{e},{a}"],
        }
        for e, a in CASES
        if answered["path"][f"{e},{a}"] != expected(e, a)
    }
    assert not wrong, f"each accumulator's share, plus the tree that combines them: {wrong}"
