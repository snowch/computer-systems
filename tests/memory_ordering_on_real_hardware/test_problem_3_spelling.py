"""Problem 18.3 — the same requirement, in two architectures' words.

The table is in the stub; the point is not memorising it. It is that the requirement is one thing
and the spellings are two, and that AArch64's release is not an instruction between two others at
all — it is a property of one of them, which a reader who learned RISC-V first will not recognise
as a barrier.
"""

from __future__ import annotations

import pytest

from tests.memory_ordering_on_real_hardware.harness import ask

TABLE = {
    ("r", "r"): "fence rw,w",
    ("a", "r"): "fence r,rw",
    ("f", "r"): "fence rw,rw",
    ("r", "a"): "stlr",
    ("a", "a"): "ldar",
    ("f", "a"): "dmb ish",
    ("x", "r"): "-",
    ("x", "a"): "-",
}


def test_one_architecture_needs_a_separate_instruction_and_one_does_not():
    """Scaffolding: the asymmetry is the lesson, so it must be in the table."""
    assert TABLE[("r", "r")].startswith("fence"), "RISC-V puts a fence between the two"
    assert TABLE[("r", "a")] == "stlr", "AArch64 folds it into the store itself"
    assert TABLE[("x", "r")] == "-", "an unknown requirement has no spelling"


@pytest.mark.problem
def test_each_requirement_has_the_spelling_the_book_saw_emitted(sharing):
    answered = ask(sharing, [f"f{need}{isa}" for need, isa in TABLE])
    wrong = {
        f"{need!r} on {isa!r}": {"expected": expected, "got": answered["spelling"][f"{need}{isa}"]}
        for (need, isa), expected in TABLE.items()
        if answered["spelling"][f"{need}{isa}"] != expected
    }
    assert not wrong, (
        f"the requirement is one thing and the spellings are two; ch17 printed both: {wrong}"
    )
