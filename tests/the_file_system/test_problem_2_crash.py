"""Problem 12.2 — what must recovery do after a crash at each stage?

Five stages, and the answer changes exactly once. Finding where is the problem, and where it is is
the entire design.
"""

from __future__ import annotations

import pytest

from tests.the_file_system.harness import NOTHING, REPLAY, ask

CASES = {0: NOTHING, 1: NOTHING, 2: REPLAY, 3: REPLAY, 4: NOTHING}


def test_the_answer_changes_exactly_once_on_the_way_up():
    """Scaffolding: a single commit point, and a transaction that is over when the header clears."""
    assert CASES[1] != CASES[2], "writing the header is what makes the transaction real"
    assert CASES[3] != CASES[4], "and clearing it is what ends it"
    assert CASES[2] == CASES[3], "between those two, replaying is always right — and harmless"


@pytest.mark.problem
def test_recovery_replays_exactly_the_committed_transactions(filesystem):
    answered = ask(filesystem, [f"c{stage}" for stage in CASES])
    names = {NOTHING: "nothing to do", REPLAY: "replay the log"}
    wrong = {
        f"crash after stage {stage}": {
            "expected": names[expected],
            "got": names.get(answered["crash"][stage], answered["crash"][stage]),
        }
        for stage, expected in CASES.items()
        if answered["crash"][stage] != expected
    }
    assert not wrong, (
        "the header is the single instant at which the transaction becomes real; before it the "
        f"log is ignorable and after it the log is authoritative: {wrong}"
    )
