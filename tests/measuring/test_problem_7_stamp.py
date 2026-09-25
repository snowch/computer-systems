"""Problem 24.7 — a stamp that can be judged later.

The distinction being checked is between a field the harness never asked for and a field the
machine could not answer. A record missing a key claims nothing; a record with a null says the
harness looked and the board declined, which is a fact about the board.
"""

from __future__ import annotations

import pytest

from bench.distribution import REQUIRED_ENVIRONMENT
from tests.measuring.judging import environment_record


@pytest.mark.problem
def test_every_field_is_present_even_when_the_machine_cannot_answer():
    partial = {"governor": "performance", "freq_khz": 2_400_000}
    record = environment_record(partial)

    missing = [field for field in REQUIRED_ENVIRONMENT if field not in record]
    assert not missing, f"the stamp never asked for {missing}"

    assert record["governor"] == "performance"
    assert record["freq_khz"] == 2_400_000
    assert record["temp_c"] is None, "a board with no sensor records None, it does not omit the key"


@pytest.mark.problem
def test_a_machine_that_answers_nothing_still_produces_a_complete_record():
    record = environment_record({})
    assert set(REQUIRED_ENVIRONMENT) <= set(record)
    assert all(record[field] is None for field in REQUIRED_ENVIRONMENT)


@pytest.mark.problem
def test_readings_are_not_invented():
    """Nothing may be filled in with a plausible default."""
    record = environment_record({"governor": "ondemand"})
    assert record["freq_khz"] is None, "a frequency nobody read is not a frequency"
