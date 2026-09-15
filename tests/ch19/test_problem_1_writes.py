"""Problem 12.1 — how many block writes does a transaction cost?

Graded against the chapter's own measurement as well as against arithmetic: the number this model
gives for the blocks the book's one-byte write logged has to be the number of writes the book
measured reaching the disk. A model that fits the formula and not the machine is not a model.
"""

from __future__ import annotations

import pytest

from bench.stamp import load_result
from tests.ch19.harness import ask

#: distinct blocks modified -> block writes that reach the disk.
CASES = {0: 0, 1: 4, 2: 6, 4: 10, 5: 12, 10: 22}


def test_the_formula_matches_what_the_book_measured():
    """Scaffolding: the target is the chapter's measurement, not a number typed here.

    The book's one-byte write logged some blocks and caused some writes. Whatever formula the
    reader arrives at has to produce the second from the first, or the chapter is wrong about its
    own figures.
    """
    alone = load_result("blocks-xv6")["summary"]["blockload"]["the_byte_alone"]
    logged, writes = alone["logged"], alone["writes"]
    assert CASES[logged] == writes, (
        f"the chapter measured {logged} blocks logged and {writes} writes; the case table says "
        f"{CASES.get(logged)}"
    )


@pytest.mark.problem
def test_every_transaction_costs_twice_its_blocks_plus_its_header(filesystem):
    answered = ask(filesystem, [f"w{blocks}" for blocks in CASES])
    wrong = {
        blocks: {"expected": expected, "got": answered["writes"][blocks]}
        for blocks, expected in CASES.items()
        if answered["writes"][blocks] != expected
    }
    assert not wrong, (
        "every block is written to the log and then to its home, and the header is written twice "
        f"around them: {wrong}"
    )
