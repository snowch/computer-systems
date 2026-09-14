"""Every declared figure renders, and says where it came from."""

from __future__ import annotations

import re

import pytest

from bench.figures import FIGURES, Diagram, Table
from bench.tables import conditions, render_table

TABLE_FIGURES = [(name, fig) for name, fig in FIGURES.items() if isinstance(fig, Table)]
DIAGRAM_FIGURES = [(name, fig) for name, fig in FIGURES.items() if isinstance(fig, Diagram)]


@pytest.mark.parametrize(("name", "figure"), TABLE_FIGURES, ids=[n for n, _ in TABLE_FIGURES])
def test_table_renders(name: str, figure: Table):
    if figure.pending:
        pytest.skip(f"{name} is waiting for the board")
    body = figure.render(figure.result)
    assert body.startswith("|"), f"{name} did not produce a markdown table"
    assert body.count("\n") >= 2, f"{name} has no rows"


@pytest.mark.parametrize(("name", "figure"), TABLE_FIGURES, ids=[n for n, _ in TABLE_FIGURES])
def test_table_carries_its_conditions(name: str, figure: Table):
    """A measurement without its conditions is an anecdote."""
    if figure.pending:
        pytest.skip(f"{name} is waiting for the board")
    caption = conditions(figure.conditions_from or figure.result)
    for required in ("target", "Source:", "code hash"):
        assert required in caption, f"{name}'s conditions line is missing {required!r}"


@pytest.mark.parametrize(("name", "figure"), DIAGRAM_FIGURES, ids=[n for n, _ in DIAGRAM_FIGURES])
def test_diagram_is_deterministic(name: str, figure: Diagram):
    """--check can only work if drawing the same figure twice produces the same bytes."""
    assert figure.draw() == figure.draw(), f"{name} is not reproducible"


@pytest.mark.parametrize(("name", "figure"), DIAGRAM_FIGURES, ids=[n for n, _ in DIAGRAM_FIGURES])
def test_diagram_is_well_formed_svg(name: str, figure: Diagram):
    from xml.etree import ElementTree  # noqa: PLC0415

    root = ElementTree.fromstring(figure.draw())
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title") is not None, (
        f"{name} has no <title>; a figure nobody can hear is a figure nobody can read"
    )


def test_render_table_escapes_nothing_it_should_not():
    body = render_table(["A", "B"], [["x", None], ["y", 1.5]])
    assert "—" in body  # None renders as an em dash, not as "None"
    assert "1.5" in body


def test_pending_fragments_contain_no_numbers():
    """A draft must never show a figure that could be mistaken for a measurement."""
    from pathlib import Path  # noqa: PLC0415

    from bench.stamp import ROOT  # noqa: PLC0415

    for name, figure in TABLE_FIGURES:
        if not figure.pending:
            continue
        fragment = Path(ROOT) / "chapters" / "_generated" / f"{name}.md"
        if not fragment.exists():
            continue
        text = "\n".join(
            line for line in fragment.read_text().splitlines() if not line.startswith("<!--")
        )
        assert not re.search(r"\b\d+(?:\.\d+)?\s*(?:ns|us|ms|s|cycles|%)\b", text), (
            f"{name} is pending but its fragment shows a figure"
        )
