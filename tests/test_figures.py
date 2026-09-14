"""Every declared figure renders, and says where it came from."""

from __future__ import annotations

import re

import pytest

from bench import stamp
from bench.figures import FIGURES, KINDS, Diagram, Listing, Table
from bench.stamp import build_result, load_result, write_result
from bench.tables import (
    board_identity_table,
    conditions,
    listing,
    listing_label,
    optimisation_level,
    render_table,
)

TABLE_FIGURES = [(name, fig) for name, fig in FIGURES.items() if isinstance(fig, Table)]
DIAGRAM_FIGURES = [(name, fig) for name, fig in FIGURES.items() if isinstance(fig, Diagram)]
LISTING_FIGURES = [(name, fig) for name, fig in FIGURES.items() if isinstance(fig, Listing)]


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
    assert figure.render() == figure.render(), f"{name} is not reproducible"


@pytest.mark.parametrize(("name", "figure"), DIAGRAM_FIGURES, ids=[n for n, _ in DIAGRAM_FIGURES])
def test_diagram_is_well_formed_svg(name: str, figure: Diagram):
    from xml.etree import ElementTree  # noqa: PLC0415

    root = ElementTree.fromstring(figure.render())
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


# -- listings -------------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "figure"), LISTING_FIGURES, ids=[n for n, _ in LISTING_FIGURES])
def test_listing_renders_from_every_result_it_names(name: str, figure: Listing):
    for result in figure.results:
        block = listing(result, figure.symbol)
        assert block.startswith("```asm"), f"{name}/{result} is not a fenced assembly block"
        assert f"<{figure.symbol}>:" in block, f"{name}/{result} does not contain its own symbol"


@pytest.mark.parametrize(("name", "figure"), LISTING_FIGURES, ids=[n for n, _ in LISTING_FIGURES])
def test_listing_label_is_read_rather_than_typed(name: str, figure: Listing):
    """Including the instruction count, which is the figure a chapter is most tempted to type."""
    for result in figure.results:
        label = listing_label(result, figure.symbol)
        arch = load_result(result)["machine"]["arch"]
        assert arch in label
        assert figure.symbol in label
        assert "instructions" in label


@pytest.mark.parametrize(("name", "figure"), LISTING_FIGURES, ids=[n for n, _ in LISTING_FIGURES])
def test_listing_results_are_listings(name: str, figure: Listing):
    """A listing figure reading a measurement would publish a number as if it were machine code."""
    for result in figure.results:
        assert load_result(result)["kind"] == "listing"


@pytest.mark.parametrize(("name", "figure"), LISTING_FIGURES, ids=[n for n, _ in LISTING_FIGURES])
def test_listing_shows_each_architecture_once(name: str, figure: Listing):
    """No two blocks in one figure may be indistinguishable from their labels.

    Originally this compared architectures alone, because comparing architectures was the only
    reason a figure had more than one block. ch21 gave it a second: the same function compiled at
    two optimisation levels, which is one architecture twice and entirely deliberate. What must
    still never happen is two blocks a reader cannot tell apart, so the key is what the label
    says — architecture and level — rather than architecture on its own.
    """
    shown = [
        (load_result(result)["machine"]["arch"], optimisation_level(load_result(result)))
        for result in figure.results
    ]
    assert len(shown) == len(set(shown)), f"{name} shows {shown} — one of them twice"


@pytest.mark.parametrize(("name", "figure"), LISTING_FIGURES, ids=[n for n, _ in LISTING_FIGURES])
def test_listing_architectures_share_a_compiler_version(name: str, figure: Listing):
    """ch00 tells the reader the two listings came from the same version of the same compiler.

    That is true of the committed results and need not stay true: regenerate them on a machine
    whose two cross compilers are a release apart and the sentence quietly becomes false while
    every other check stays green. This is the one that notices.
    """
    versions = {load_result(result)["toolchain"]["cc"].split()[-1] for result in figure.results}
    assert len(versions) == 1, f"{name} compares listings from gcc {sorted(versions)}"


def test_listing_refuses_a_measurement():
    with pytest.raises(ValueError, match="not a listing"):
        listing("setup-xv6", "sysfs_clamp")


def test_listing_names_the_symbols_it_has():
    with pytest.raises(KeyError, match="sysfs_clamp"):
        listing("shapes-aarch64", "no_such_function")


def test_every_figure_has_a_renderer():
    """A figure kind the renderer does not know would vanish from a chapter silently."""
    for name, figure in FIGURES.items():
        assert isinstance(figure, KINDS), (
            f"{name} is a {type(figure).__name__}, which nothing renders"
        )


# -- the board table, on a board the author does not have ------------------------------------

#: What each architecture's kernel reports about its own core. Both are in the shape
#: ``/proc/cpuinfo`` actually uses; neither machine is attached to CI, so the only way to know
#: the table works on both is to hand it both.
CPUINFO = {
    "aarch64": {
        "cpu implementer": "0x41",
        "cpu architecture": "8",
        "cpu part": "0xd0b",
        "cpu revision": "1",
        "features": "fp asimd evtstrm aes pmull crc32 atomics",
        "bogomips": "108.00",
    },
    "riscv64": {
        "isa": "rv64imafdc_zicntr",
        "uarch": "sifive,u74-mc",
        "mmu": "sv39",
        "mvendorid": "0x489",
        "marchid": "0x8000000000000007",
        "mimpid": "0x4210427",
    },
}


@pytest.fixture
def board_result(tmp_path, monkeypatch):
    """Write a plausible `setup-host` for one architecture and point the loader at it."""

    def make(arch: str):
        payload = build_result(
            name="setup-host",
            target="host",
            summary={
                "perf_counters_readable": True,
                "perf_cycles_event": "cycles",
                "perf_can_sample": arch == "aarch64",
                "perf_samples": 214 if arch == "aarch64" else 0,
            },
            code_sources=["bench/run_setup.py"],
            toolchain={"cc": "gcc (test) 13.3.0", "flags": "-O2"},
            machine={
                "kind": "board",
                "arch": arch,
                "measured_under": "native",
                "model": f"a {arch} board",
                "os": "Some Linux 1.0",
                "kernel": "Linux 6.6",
                "cpus_online": "0-3",
                "cpu": CPUINFO[arch],
            },
        )
        write_result(payload, results_dir=tmp_path)
        monkeypatch.setattr(stamp, "RESULTS_DIR", tmp_path)
        return payload

    return make


@pytest.mark.parametrize("arch", sorted(CPUINFO))
def test_board_table_describes_either_architecture(arch: str, board_result):
    """The reference machine is ARM; a reader may follow Part III on a RISC-V board.

    A table hard-coded to one of them prints a column of dashes on the other, which reads as a
    broken measurement rather than a different machine. This is the check that the author, who
    has neither board to hand, can still run.
    """
    board_result(arch)
    table = board_identity_table("setup-host")
    assert "—" not in table, f"the {arch} table has an empty cell:\n{table}"
    for value in CPUINFO[arch].values():
        if value == "108.00":
            continue  # bogomips is deliberately skipped
        assert value in table, f"{arch}: {value!r} is missing from the table"


def test_board_table_skips_bogomips(board_result):
    """It is a kernel calibration loop, not a fact about the core."""
    board_result("aarch64")
    assert "108.00" not in board_identity_table("setup-host")


def test_board_table_reports_counting_and_sampling_separately(board_result):
    """ch00's central claim about the hardware: a core can count and still not sample."""
    board_result("riscv64")
    table = board_identity_table("setup-host")
    assert "| `perf stat` reads hardware counters | yes |" in table
    assert "| `perf record` can sample | no |" in table


def test_board_table_names_the_configuration_not_only_the_board(board_result):
    """The reference board's own PMU went missing for a kernel release (ch00, @rpi-pmu-dt-6507).

    So "which board" is not the whole answer to "do the counters work": the image and the kernel
    are part of the configuration the numbers came from, and the table a reader compares against
    has to say which ones.
    """
    board_result("aarch64")
    table = board_identity_table("setup-host")
    assert "| Operating system | Some Linux 1.0 |" in table
    assert "| Kernel | Linux 6.6 |" in table


def test_board_table_shows_how_many_samples_the_check_collected(board_result):
    """A sampling claim backed by an exit status is not backed by anything (ch00)."""
    board_result("aarch64")
    assert "| Samples collected in the capability check | 214 |" in board_identity_table(
        "setup-host"
    )
