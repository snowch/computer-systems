"""Checks Problem 0.2 by asking the compiler, on whatever RV64 path this machine has."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench.measure import compile_program
from bench.stamp import ROOT
from tests.ch00.problem_2_abi import EXPECTED_ALIGN, EXPECTED_OFFSETS, EXPECTED_SIZE

SOURCE = ROOT / "tests" / "ch00" / "abi_puzzle.c"

pytestmark = pytest.mark.hostcode


@pytest.fixture(scope="module")
def measured(host_target, build_dir: Path) -> dict[str, int]:
    built = compile_program([SOURCE], build_dir / "abi_puzzle", host_target)
    facts: dict[str, int] = {}
    for line in built.run().stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            facts[parts[0]] = int(parts[1])
        elif len(parts) == 3 and parts[0] == "offset":
            facts[f"offset.{parts[1]}"] = int(parts[2])
    assert facts, "the puzzle program printed nothing"
    return facts


def _unanswered(value) -> bool:
    return value is None


@pytest.mark.problem
def test_size(measured: dict[str, int]):
    if _unanswered(EXPECTED_SIZE):
        pytest.fail("Problem 0.2: EXPECTED_SIZE is still None")
    assert measured["size"] == EXPECTED_SIZE


@pytest.mark.problem
def test_alignment(measured: dict[str, int]):
    if _unanswered(EXPECTED_ALIGN):
        pytest.fail("Problem 0.2: EXPECTED_ALIGN is still None")
    assert measured["align"] == EXPECTED_ALIGN


@pytest.mark.parametrize("member", ["flag", "count", "id", "code", "tag"])
@pytest.mark.problem
def test_offset(member: str, measured: dict[str, int]):
    expected = EXPECTED_OFFSETS.get(member)
    if _unanswered(expected):
        pytest.fail(f"Problem 0.2: EXPECTED_OFFSETS[{member!r}] is still None")
    assert measured[f"offset.{member}"] == expected, (
        f"{member} is not where you thought. The padding between two members is whatever it "
        "takes to satisfy the alignment of the one that comes second."
    )


def test_the_puzzle_builds_and_reports(measured: dict[str, int]):
    """Scaffolding: the problem is answerable on this machine.

    Also the reason the question is worth asking — the struct is bigger than its members, and
    nobody asked for the difference.
    """
    assert set(measured) == {
        "size",
        "align",
        "offset.flag",
        "offset.count",
        "offset.id",
        "offset.code",
        "offset.tag",
    }
    assert measured["size"] > 1 + 8 + 4 + 2 + 1
