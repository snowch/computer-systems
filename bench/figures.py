"""Every figure the book contains, declared in one place.

One entry per table and per diagram, so a chapter cannot quietly cite a different run than the
one its prose discusses. ``scripts/render-figures.py`` turns these into files under
``chapters/_generated/`` and ``chapters/_figures/``, which chapters pull in with ``{include}``
and ``{figure}``; ``scripts/verify-numbers.py`` fails the build when a committed fragment no
longer matches what the results say.

## Pending figures

Part III is measured on hardware that is not attached to CI and never will be. A figure whose
measurement has not been taken yet is declared here with a ``pending`` reason, and renders as a
warning naming the command that would produce it. That is deliberately not the same thing as a
placeholder number:

* nothing is invented — the fragment contains no figures at all, so a draft can never be mistaken
  for a measurement, in the site or in the PDF;
* the prose around it is written as though the numbers were there, so landing them is a
  one-command change rather than a rewrite;
* ``verify-numbers.py`` **fails** if a pending figure's result file exists, so a measurement that
  has landed cannot be left marked as missing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bench import tables
from bench.diagrams import two_target_map


@dataclass(frozen=True)
class Table:
    """A markdown fragment rendered from one committed result."""

    render: Callable[[str], str]
    result: str
    #: None means "take the conditions line from `result`"; a name overrides it.
    conditions_from: str | None = None
    #: Why this has not been measured, and what to run. None means it has been.
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.pending is None else ()


@dataclass(frozen=True)
class Diagram:
    """An SVG figure drawn by :mod:`bench.diagrams`."""

    draw: Callable[[], str]
    alt: str

    @property
    def sources(self) -> tuple[str, ...]:
        return ()


#: The board runs Part III. Repeating the instruction in every pending reason would be noise, so
#: it lives here and each entry says what specifically is missing.
BOARD = "run `make bench-board` on the VisionFive 2 Lite and commit the result"

FIGURES: dict[str, Table | Diagram] = {
    # -- ch00 ---------------------------------------------------------------------------
    "ch00-targets": Diagram(
        draw=two_target_map,
        alt="The xv6 and host targets side by side, with what each can and cannot answer.",
    ),
    "ch00-xv6-environment": Table(
        render=tables.xv6_environment_table,
        result="setup-xv6",
    ),
    "ch00-probe-types": Table(
        render=tables.probe_types_table,
        result="setup-xv6",
    ),
    "ch00-probe-layouts": Table(
        render=tables.probe_layout_table,
        result="setup-xv6",
    ),
    "ch00-board": Table(
        render=tables.board_identity_table,
        result="setup-host",
        pending=f"The board has not reported yet: {BOARD} (`bench/results/setup-host.json`).",
    ),
}


def cited_results() -> set[str]:
    """Every result file a figure reads. Pending figures cite nothing, by definition."""
    return {name for figure in FIGURES.values() for name in figure.sources}


def pending_results() -> dict[str, str]:
    """Result name -> the reason its figure is still waiting for it."""
    return {
        figure.result: figure.pending
        for figure in FIGURES.values()
        if isinstance(figure, Table) and figure.pending is not None
    }
