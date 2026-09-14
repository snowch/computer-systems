"""Problem 15.1 — where does the curve step?

The curves are synthetic and their steps are therefore known by construction: the test builds a
three-level machine with boundaries it chose, and asks the reader to find them back.
"""

from __future__ import annotations

import pytest

from tests.ch15.harness import ask, curve

FACTOR = 15  # a step is half again as slow as the point before it

#: A machine with three levels. The numbers are this test's invention and no board's.
CURVES = {
    "three levels": (
        [(32, 2), (64, 2), (128, 2), (256, 8), (512, 8), (1024, 40), (2048, 40), (4096, 120)],
        [256, 1024, 4096],
    ),
    "no steps at all": ([(32, 5), (64, 5), (128, 5), (256, 5)], []),
    "one gentle rise that is not a step": ([(32, 10), (64, 11), (128, 12)], []),
    "a step at the very end": ([(32, 3), (64, 3), (128, 90)], [128]),
}


def test_the_curves_include_a_rise_that_must_not_count():
    """Scaffolding: a curve that drifts upward has no steps, or the threshold means nothing."""
    assert CURVES["one gentle rise that is not a step"][1] == []
    assert len(CURVES["three levels"][1]) == 3


@pytest.mark.problem
def test_every_step_and_only_the_steps_are_found(hierarchy):
    names = sorted(CURVES)
    commands = []
    for i, name in enumerate(names):
        points, _ = CURVES[name]
        xs, ys = curve(points)
        commands.append(f"s{i},{FACTOR},{xs},{ys}")
    answered = ask(hierarchy, commands)
    wrong = {
        name: {"expected": CURVES[name][1], "got": answered["steps"][i]}
        for i, name in enumerate(names)
        if answered["steps"][i] != CURVES[name][1]
    }
    assert not wrong, (
        f"a step is a point at least {FACTOR} tenths slower than the one before it, and a curve "
        f"that merely drifts upward has none: {wrong}"
    )
