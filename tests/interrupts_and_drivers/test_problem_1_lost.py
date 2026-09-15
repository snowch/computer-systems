"""Problem 9.1 — how many characters does the console lose?

Every answer follows from the event string the test wrote, so nothing is stored. The buffer size
is xv6's own, so a reader who wants to check an answer against the real kernel can.
"""

from __future__ import annotations

import pytest

from tests.interrupts_and_drivers.harness import BUF, ask

FULL = "+" * BUF

CASES = {
    "": 0,
    "+": 0,
    "+++9": 0,
    FULL: 0,
    FULL + "+": 1,
    FULL + "+++": 3,
    # Drain some, and exactly that many more fit.
    FULL + "9" + "+" * 9: 0,
    FULL + "9" + "+" * 10: 1,
    # A drain of more than is there empties it and no more.
    "+++" + "9" + FULL: 0,
    "+++" + "9" + FULL + "+": 1,
    # Draining an empty buffer is not an error and does not create room in advance.
    "9" + FULL + "+": 1,
}


def test_the_cases_include_both_sides_of_the_boundary():
    """Scaffolding: a full buffer loses nothing and one more character loses one."""
    assert CASES[FULL] == 0 and CASES[FULL + "+"] == 1
    assert max(CASES.values()) > 1, "at least one case must lose more than a single character"
    assert any(v == 0 for k, v in CASES.items() if len(k) > BUF), (
        "draining must actually make room, or the problem is just a maximum"
    )


@pytest.mark.problem
def test_the_model_loses_what_the_buffer_cannot_hold(console):
    ordered = list(CASES)
    answered = ask(console, [f"l{events}" for events in ordered])
    wrong = {
        (events[:12] + "…" if len(events) > 12 else events) or "(no events)": {
            "expected": CASES[events],
            "got": answered["lost"][position + 1],
        }
        for position, events in enumerate(ordered)
        if answered["lost"][position + 1] != CASES[events]
    }
    assert not wrong, (
        f"the buffer holds {BUF}; a character arriving when it is full is dropped and nothing is "
        f"told: {wrong}"
    )
