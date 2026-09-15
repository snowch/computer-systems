"""Problem 15.2 — what is the line size?

Synthetic stride curves whose flat region the test chose, so the answer is known by construction.
The curve with no rise at all has no answer, and saying so is the right answer.
"""

from __future__ import annotations

import pytest

from tests.the_memory_hierarchy.harness import ask, curve

FACTOR = 15

CURVES = {
    "lines of 64": ([(8, 1), (16, 1), (32, 1), (64, 4), (128, 8)], 64),
    "lines of 128": ([(8, 2), (16, 2), (32, 2), (64, 2), (128, 9)], 128),
    "flat throughout": ([(8, 3), (16, 3), (32, 3), (64, 3)], 0),
}


def test_a_flat_curve_has_no_line_size_to_report():
    """Scaffolding: the problem must have a "no answer" case or it is a maximum-finder."""
    assert CURVES["flat throughout"][1] == 0
    assert len({answer for _, answer in CURVES.values()}) == 3


@pytest.mark.problem
def test_the_line_is_the_stride_at_which_the_curve_first_rises(hierarchy):
    names = sorted(CURVES)
    commands = []
    for i, name in enumerate(names):
        points, _ = CURVES[name]
        xs, ys = curve(points)
        commands.append(f"l{i},{FACTOR},{xs},{ys}")
    answered = ask(hierarchy, commands)
    wrong = {
        name: {"expected": CURVES[name][1], "got": answered["line"][i]}
        for i, name in enumerate(names)
        if answered["line"][i] != CURVES[name][1]
    }
    assert not wrong, f"the first stride at which consecutive visits stop sharing a line: {wrong}"
