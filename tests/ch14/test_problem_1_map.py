"""Problem 7.1 — build a page table, and no more of one than the addresses require.

Graded against `sysfs/tools/sv39.c`, which counts what a set of runs costs without knowing how to
build anything. So the target is not a stored number: it is derived, at test time, from the same
model the chapter measures a real kernel against.
"""

from __future__ import annotations

import pytest

from tests.ch14.harness import PAGE, ask, maps, run_of, tables_needed

#: Three address spaces with the same number of pages in them and different shapes. If the reader
#: has understood the chapter, all three counts follow; if they have written a mapper that
#: allocates a level for every page, the first passes and the others do not.
SHAPES = {
    "one run": [(0x0, 8)],
    "two ends": [(0x0, 4), (0x3FFFFFE000, 4)],
    "scattered": [(0x0, 2), (0x40000000, 2), (0x80000000, 2), (0xC0000000, 2)],
}


def _session(shape):
    pairs, physical = [], 0x10000
    for start, pages in shape:
        pairs += run_of(start, pages, physical)
        physical += pages * PAGE
    return pairs


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_the_model_gives_each_shape_a_different_answer(name, build_dir):
    """Scaffolding: the oracle is real, and it distinguishes the three shapes.

    Unmarked, so CI keeps checking that this problem has a target — and that the target is not
    the same number three times, which would make the problem trivially passable.
    """
    counts = {key: tables_needed(build_dir, SHAPES[key]) for key in SHAPES}
    assert counts[name] >= 3, "every address space needs a root and at least one chain"
    assert len(set(counts.values())) == len(counts), (
        f"the three shapes must cost differently or the problem is not a problem: {counts}"
    )


@pytest.mark.problem
@pytest.mark.parametrize("name", sorted(SHAPES))
def test_the_mapper_allocates_exactly_what_the_addresses_require(name, walk, build_dir):
    shape = SHAPES[name]
    answered = ask(walk, maps(_session(shape)))
    assert set(answered["map"].values()) == {0}, (
        f"walk_map reported a failure for {name}: {answered['map']}"
    )
    assert answered["allocated"] == tables_needed(build_dir, shape), (
        f"{name}: the model derives {tables_needed(build_dir, shape)} page-table pages from these "
        f"addresses and walk_map took {answered['allocated']}"
    )
