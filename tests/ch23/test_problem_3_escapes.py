"""Checks Problem 16.3 by compiling the file and counting.

The key is the compiler's own behaviour, obtained at test time. A function whose loop survived is
many instructions long; one whose loop was removed is a handful. The threshold is set from the
data rather than fixed, so a different compiler moves the answer rather than breaking the test.
"""

from __future__ import annotations

import pytest

from bench.disasm import disassemble
from bench.measure import HostTarget
from bench.run_disasm import flags_for, target_for
from tests.ch23.problem_3_escapes import SURVIVES

SOURCE = "tests/ch23/escapes.c"
ARCH = "aarch64"


def measured() -> dict[str, int]:
    base = target_for(ARCH)
    flags = tuple(f for f in flags_for(ARCH) if not f.startswith("-O")) + ("-O2",)
    target = HostTarget(name="ch23escapes", cc=base.cc, flags=flags)
    return {name: disassemble([SOURCE], name, target).instructions for name in SURVIVES}


def survived(counts: dict[str, int]) -> dict[str, bool]:
    """A loop that was kept is an order of magnitude longer than one that was not.

    The threshold is the midpoint between the largest and smallest function, in logarithmic terms,
    so it follows the compiler rather than being a number this test asserts.
    """
    smallest, largest = min(counts.values()), max(counts.values())
    threshold = (smallest + largest) / 2
    return {name: value > threshold for name, value in counts.items()}


@pytest.mark.hostcode
def test_the_compiler_keeps_some_of_them_and_not_others():
    """Scaffolding: if it kept all five or none, there is nothing to predict."""
    counts = measured()
    kept = survived(counts)
    assert 0 < sum(kept.values()) < len(kept), (
        f"the compiler must disagree about these or the problem is empty: {counts}"
    )


@pytest.mark.hostcode
@pytest.mark.problem
def test_the_prediction_matches_what_the_compiler_did():
    unanswered = sorted(name for name, value in SURVIVES.items() if value is None)
    assert not unanswered, f"still to answer: {unanswered}"

    counts = measured()
    truth = survived(counts)
    wrong = {
        name: {"you said": SURVIVES[name], "it was": truth[name], "instructions": counts[name]}
        for name in SURVIVES
        if SURVIVES[name] != truth[name]
    }
    assert not wrong, (
        "a compiler may remove work whose result nothing can observe, and a benchmark whose work "
        f"has been removed reports a speedup that never happened: {wrong}"
    )
