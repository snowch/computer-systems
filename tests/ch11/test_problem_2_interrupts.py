"""Problem 9.2 — how many interrupts will this cost, and when is that not a question?

The arithmetic cases follow from the numbers the test supplies. The last case is the chapter: a
device that interrupts to say it is ready rather than to say it is finished gives a count that the
workload does not decide, and saying so is a better answer than any number.
"""

from __future__ import annotations

import pytest

from tests.ch11.harness import UNDECIDABLE, ask

CASES = {
    (0, 1): 0,
    (1, 1): 1,
    (64, 1): 64,
    (64, 8): 8,
    (64, 64): 1,
    (65, 8): 9,  # the last batch is short and still costs an interrupt
    (7, 8): 1,
    # per_interrupt of zero is the character device: "ready for more", not "this is finished".
    (64, 0): UNDECIDABLE,
    (0, 0): UNDECIDABLE,
}


def test_the_cases_include_a_short_batch_and_the_undecidable_one():
    """Scaffolding: division alone is not enough, and one case has no numeric answer."""
    assert CASES[(65, 8)] == 9, "a short final batch still costs one"
    assert UNDECIDABLE in CASES.values(), "the point of the problem must be reachable"
    assert len({v for v in CASES.values() if v != UNDECIDABLE}) > 3


@pytest.mark.problem
def test_the_count_follows_the_completions_except_when_it_cannot(console):
    answered = ask(console, [f"i{completions},{per}" for completions, per in CASES])
    wrong = {
        f"{completions} completions, {per} per interrupt": {
            "expected": "undecidable" if expected == UNDECIDABLE else expected,
            "got": "undecidable"
            if answered["interrupts"][key] == UNDECIDABLE
            else answered["interrupts"][key],
        }
        for key, expected in CASES.items()
        for completions, per in [key]
        if answered["interrupts"][key] != expected
    }
    assert not wrong, (
        "a device that reports completions gives a count the workload decides; one that reports "
        f"readiness does not: {wrong}"
    )
