"""The measurements that need the board, checked as far as they can be without one.

Nothing here takes a timing. What it checks is the part that is normally only discovered on the
day the hardware arrives: that a runner exists for every figure still waiting, and that what the
runner writes is the shape the chapter's table reads.

Getting that wrong costs nothing today and costs the whole session on the one day the board is
available, which is why these are tests rather than a checklist.
"""

from __future__ import annotations

import importlib
import json

import pytest

from bench.figures import FIGURES, Table, pending_results
from bench.stamp import RESULTS_DIR
from bench.tables import render_table  # noqa: F401  — imported so a broken tables.py fails here

#: Result name -> the module that produces it.
BOARD_RUNNERS = {
    "setup-host": "bench.run_setup",
    "measuring-host": "bench.run_measuring",
    "hierarchy-host": "bench.run_hierarchy",
    "bridge-host": "bench.run_bridgecost",
    "loops-host": "bench.run_loopcost",
    "pipeline-host": "bench.run_pipelinecost",
    "vectors-host": "bench.run_vectorcost",
    "sharing-host": "bench.run_sharingcost",
}

#: Figures still waiting for a runner to be written, not just for the board to exist.
#:
#: This list is a debt, and it is here rather than in a document because a document would not
#: fail. Every entry is a chapter that cannot be completed on the day the hardware arrives.
#: Delete a name when its runner lands; the test below fails if one is deleted too early, and
#: `test_the_debt_list_is_not_padded` fails if one is left here after its runner exists.
RUNNER_NOT_WRITTEN = {
    "faultcost-host",
    "oscost-host",
    "profile-host",
    "skid-host",
    "vdso-host",
}


def test_every_pending_result_has_a_runner_or_is_a_declared_debt():
    """The check that would have caught it.

    Twelve of the thirteen pending results had no code that could produce them, and nothing said
    so: `make bench-board` would have run, written one file, and left every Part IV figure
    pending with no way to fill it. A pending figure is a promise, and a promise needs something
    that can keep it.
    """
    unaccounted = set(pending_results()) - set(BOARD_RUNNERS) - RUNNER_NOT_WRITTEN
    assert not unaccounted, (
        f"these figures are marked pending but nothing produces them and they are not on the "
        f"debt list: {sorted(unaccounted)}"
    )


def test_the_debt_list_is_not_padded():
    """A debt list nobody removes from is a list nobody reads."""
    settled = RUNNER_NOT_WRITTEN & set(BOARD_RUNNERS)
    assert not settled, (
        f"these have runners now and should come off the debt list: {sorted(settled)}"
    )

    gone = RUNNER_NOT_WRITTEN - set(pending_results())
    assert not gone, f"these are on the debt list but are no longer pending figures: {sorted(gone)}"


@pytest.mark.parametrize("result", sorted(BOARD_RUNNERS))
def test_a_runner_declares_the_shape_it_will_write(result: str):
    """Every board runner but `setup-host` publishes the summary it produces, for the test below.

    `run_setup` predates this and writes a summary shared with its xv6 half, so it is exempt.
    """
    if result == "setup-host":
        pytest.skip("run_setup predates the shape contract and shares its summary with xv6")
    module = importlib.import_module(BOARD_RUNNERS[result])
    assert hasattr(module, "SHAPE"), f"{BOARD_RUNNERS[result]} declares no SHAPE"
    assert isinstance(module.SHAPE, dict) and module.SHAPE


def _figures_for(result: str) -> list[tuple[str, Table]]:
    return [
        (name, figure)
        for name, figure in FIGURES.items()
        if isinstance(figure, Table) and figure.result == result
    ]


@pytest.mark.parametrize("result", sorted(set(BOARD_RUNNERS) - {"setup-host"}))
def test_the_shape_a_runner_writes_is_the_shape_its_tables_read(result: str, monkeypatch):
    """Render every table that cites this result, against the summary its runner will produce.

    This is the whole point of the file. A runner and a renderer that disagree about a key are
    two files that each look correct, and the disagreement surfaces as a KeyError on the one
    afternoon the board is plugged in.
    """
    module = importlib.import_module(BOARD_RUNNERS[result])
    figures = _figures_for(result)
    assert figures, f"{result} has a runner but no figure cites it"

    fake = {
        "summary": module.SHAPE,
        "code_fingerprint": "shape-check",
        "machine": {},
        "toolchain": {},
    }
    monkeypatch.setattr("bench.tables.load_result", lambda _name: fake)

    for name, figure in figures:
        rendered = figure.render(result)
        assert rendered.strip(), f"{name} rendered nothing from {BOARD_RUNNERS[result]}'s SHAPE"


def test_no_committed_result_is_a_shape_fixture():
    """The fixtures are contract examples and must never become measurements.

    They are full of 111 and 222 precisely so that one reaching `bench/results/` would be
    obvious, and this is what makes it obvious.
    """
    shapes = {}
    for result, module_name in BOARD_RUNNERS.items():
        module = importlib.import_module(module_name)
        if hasattr(module, "SHAPE"):
            shapes[result] = module.SHAPE
    for result, shape in shapes.items():
        path = RESULTS_DIR / f"{result}.json"
        if path.exists():
            assert json.loads(path.read_text())["summary"] != shape, (
                f"{path.name} contains the shape fixture rather than a measurement"
            )
