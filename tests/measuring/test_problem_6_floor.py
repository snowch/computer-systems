"""Problem 24.6 — a timing shorter than the clock that took it.

The case the chapter insists on is the last one: a measured region below the timer's own overhead
is not a fast measurement. There is nothing in it but instrument.
"""

from __future__ import annotations

import pytest

from tests.measuring.judging import reportable

OVERHEAD = 20.0

# (measured region, may it be published, why)
CASES = [
    (5.0, False, "shorter than the timer overhead: this is the clock, not the work"),
    (20.0, False, "exactly the overhead, so half of any answer is instrument"),
    (200.0, False, "ten times the overhead, still well under the factor this book requires"),
    (1_999.0, False, "just under the bar"),
    (2_000.0, True, "exactly the factor the chapter derives"),
    (500_000.0, True, "comfortably above it"),
]


@pytest.mark.problem
@pytest.mark.parametrize(("measured", "allowed", "why"), CASES)
def test_a_region_must_be_larger_than_the_instrument(measured, allowed, why):
    assert reportable(measured, OVERHEAD) is allowed, why


@pytest.mark.problem
def test_a_timing_below_the_overhead_is_never_reportable():
    """Whatever factor is asked for, a region under the clock's own cost cannot be published."""
    for factor in (1.0, 10.0, 100.0, 1000.0):
        assert reportable(OVERHEAD / 2, OVERHEAD, factor=factor) is False
