"""Problem 18.2 — what does the scaling curve look like before you measure it?

Amdahl's law, computed by the test from the same parameters. The case worth sitting with is a
quarter of the work being serial: four cores then buy a speedup of about two and a quarter, and a
thousand cores cannot buy four.
"""

from __future__ import annotations

import pytest

from tests.ch25.harness import ask

CASES = [
    (100, 1, 0),
    (100, 4, 0),
    (100, 4, 25),
    (100, 4, 50),
    (100, 2, 50),
    (100, 1000, 10),
    (100, 1000, 25),
]


def expected(total: int, threads: int, serial_percent: int) -> int:
    serial = serial_percent / 100
    return int(100 / (serial + (1 - serial) / threads))


def test_the_serial_fraction_dominates_before_the_core_count_does():
    """Scaffolding: the ceiling has to be visible, or the problem is just division."""
    assert expected(100, 4, 0) == 400, "with nothing serial, four cores give four"
    assert expected(100, 4, 25) < 250, "with a quarter serial, four cores give barely over two"
    assert expected(100, 1000, 25) < 400, "and no number of cores passes four"
    assert expected(100, 1000, 10) < 1000, "a tenth serial caps it at ten, however many cores"


@pytest.mark.problem
def test_the_predicted_speedup_is_amdahls(sharing):
    answered = ask(sharing, [f"s{t},{n},{s}" for t, n, s in CASES])
    wrong = {
        f"{n} threads, {s}% serial": {
            "expected": expected(t, n, s),
            "got": answered["speedup"][f"{t},{n},{s}"],
        }
        for t, n, s in CASES
        if answered["speedup"][f"{t},{n},{s}"] != expected(t, n, s)
    }
    assert not wrong, f"the serial part takes as long as it ever did and the rest divides: {wrong}"
