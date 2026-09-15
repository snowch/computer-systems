"""Problem 7.2 — follow the page table your 7.1 built.

The expected answers are the mappings the test itself asked for, so nothing is stored: the target
is whatever the reader's mapper was told to arrange. An address deliberately left unmapped must
fault, because a translation that succeeds everywhere is not a translation.
"""

from __future__ import annotations

import pytest

from tests.ch09.harness import PAGE, ask, maps, run_of

#: Two runs at opposite ends of the address space, as init's own are. The physical addresses are
#: arbitrary and deliberately not equal to the virtual ones: an implementation that returns its
#: argument passes a lazier test than this one.
MAPPED = run_of(0x0, 4, 0x2A000) + run_of(0x3FFFFFE000, 2, 0x71000)

#: Inside a mapped region's table, in a mapped gigabyte, and in an empty one.
UNMAPPED = (0x9000, 0x00400000, 0x40000000)

#: A byte that is not at the start of its page, because the offset is the part translation is
#: supposed to leave alone.
WITHIN_PAGE = 0x123


def test_the_test_asks_about_addresses_it_actually_mapped(walk):
    """Scaffolding: the questions and the mappings agree, and the unmapped ones really are."""
    mapped = {va for va, _ in MAPPED}
    assert not mapped & set(UNMAPPED), "an 'unmapped' probe is in the mapped set"
    assert len(mapped) == len(MAPPED), "the same page is mapped twice"
    assert 0 < WITHIN_PAGE < PAGE


@pytest.mark.problem
def test_every_mapped_address_translates_to_what_it_was_mapped_to(walk):
    probes = [f"t{va + WITHIN_PAGE:#x}" for va, _ in MAPPED]
    answered = ask(walk, maps(MAPPED) + probes)
    for va, pa in MAPPED:
        got = answered["translate"][va + WITHIN_PAGE]
        assert got == pa + WITHIN_PAGE, (
            f"{va + WITHIN_PAGE:#x} was mapped to {pa:#x} and walk_translate said "
            f"{'fault' if got is None else hex(got)}"
        )


@pytest.mark.problem
def test_an_unmapped_address_faults(walk):
    answered = ask(walk, maps(MAPPED) + [f"t{va:#x}" for va in UNMAPPED])
    for va in UNMAPPED:
        assert answered["translate"][va] is None, (
            f"{va:#x} was never mapped and walk_translate returned {answered['translate'][va]:#x}"
        )
