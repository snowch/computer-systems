"""Checks Problem 6.1 by running the reader's program and reading its own report."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare
from bench.stamp import load_result
from tests.one_page_table_two_harts.problem_1_four_kilobytes import WHAT_MAKES_AN_ENTRY_A_LEAF

ANSWER = Path(__file__).parent / "answer_page.c"


def test_the_chapters_table_used_three_entries():
    """Scaffolding: the arrangement being replaced is the one the chapter measured."""
    assert load_result("paging-bare")["summary"]["entries_used"] == 3


@pytest.mark.problem
def test_the_alias_still_works_through_a_real_walk(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 6.1: put your program in {ANSWER.name} beside this test"

    image = bare.build_from([ANSWER], "problem_page", build_dir=tmp_path)
    fields = bare.run("paging", image=image, timeout=30).fields()
    assert fields.get("alias_reads_the_same") == 1, "the alias no longer reads the same byte"
    assert fields.get("top_entry_is_a_leaf") == 0, (
        "the top-level entry is still a leaf, so it is still mapping a gigabyte"
    )
    assert fields.get("levels_walked", 0) >= 2, "a four-kilobyte mapping needs more than one level"


@pytest.mark.problem
def test_the_reader_can_say_what_a_leaf_is():
    assert len(WHAT_MAKES_AN_ENTRY_A_LEAF.split()) >= 4, (
        "Problem 6.1: WHAT_MAKES_AN_ENTRY_A_LEAF wants a phrase"
    )
