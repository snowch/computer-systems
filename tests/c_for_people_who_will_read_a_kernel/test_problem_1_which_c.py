"""Checks Problem 3.1 by compiling every candidate and disassembling it.

No listings are stored. The test builds each candidate, captures what the compiler emitted, and
hands the reader those listings under opaque names — so the puzzle is generated from the same
toolchain the reader has, and cannot go stale or disagree with their machine.
"""

from __future__ import annotations

import hashlib

import pytest

from bench.disasm import disassemble
from bench.run_disasm import target_for
from tests.c_for_people_who_will_read_a_kernel.problem_1_which_c import ANSWERS, CANDIDATES


def _label(name: str) -> str:
    """A stable, uninformative name for a listing, so the puzzle is not its own answer key."""
    return "listing_" + hashlib.sha256(name.encode()).hexdigest()[:6]


@pytest.fixture(scope="module")
def listings(tmp_path_factory) -> dict[str, str]:
    """Compile each candidate on its own and return {opaque label: what came out}."""
    directory = tmp_path_factory.mktemp("whichc")
    target = target_for("riscv64")
    out: dict[str, str] = {}
    for name, source in CANDIDATES.items():
        path = directory / f"{_label(name)}.c"
        path.write_text(source + "\n")
        out[_label(name)] = disassemble(
            [str(path)], "f", target, includes=[], build_dir=directory
        ).text
    return out


@pytest.mark.problem
def test_the_reader_answered_every_listing(listings):
    assert ANSWERS, "Problem 3.1: ANSWERS is still empty"
    assert set(ANSWERS) == set(listings), (
        f"answer every listing exactly once. They are: {sorted(listings)}"
    )
    assert sorted(ANSWERS.values()) == sorted(CANDIDATES), "use each candidate exactly once"


@pytest.mark.problem
@pytest.mark.parametrize("candidate", sorted(CANDIDATES))
def test_the_reader_matched_the_right_listing(candidate: str, listings):
    assert ANSWERS, "Problem 3.1: ANSWERS is still empty"
    chosen = [label for label, name in ANSWERS.items() if name == candidate]
    assert chosen == [_label(candidate)], (
        f"you matched {candidate!r} to {chosen or 'nothing'}. Compile it and compare:\n"
        f"{CANDIDATES[candidate]}"
    )


def test_the_four_listings_are_distinguishable(listings):
    """Scaffolding: a puzzle with two identical listings in it has no answer.

    Worth checking rather than assuming — `sysfs_sum_array` and `sysfs_sum_pointer` in this
    chapter compile to exactly the same instructions, which is the section those two are in.
    """
    bodies = {text.split(">:", 1)[1] for text in listings.values()}
    assert len(bodies) == len(listings), "two candidates compiled to the same thing"
