"""Checks Problem 6.1 by booting the reader's kernel and running the reader's program.

The test cannot check that the number is *correct* without reimplementing the counter, so it
checks the two things that distinguish a real system call from a plausible stub: that the value
is not zero, and that it grows when the program makes more system calls. A constant passes
neither.
"""

from __future__ import annotations

import re

import pytest

from bench import xv6
from bench.stamp import ROOT
from tests.ch06.problem_1_addcall import PROGRAM

_COUNT = re.compile(r"^trapcount (\d+)$", re.MULTILINE)

pytestmark = pytest.mark.xv6


@pytest.fixture(scope="module")
def transcript():
    if PROGRAM is None:
        pytest.fail("Problem 6.1: PROGRAM is still None")
    if not (ROOT / "xv6" / "apps" / f"{PROGRAM}.c").exists():
        pytest.fail(f"xv6/apps/{PROGRAM}.c does not exist")
    result = xv6.boot([PROGRAM, PROGRAM])
    assert not result.timed_out, result.transcript[-1500:]
    return result.transcript


@pytest.mark.problem
def test_the_program_reports_a_count(transcript):
    counts = _COUNT.findall(transcript)
    assert counts, (
        "no line of the form `trapcount <number>` appeared. The program must print exactly that."
    )
    assert int(counts[0]) > 0, "the count was zero — the kernel has served system calls by now"


@pytest.mark.problem
def test_the_count_is_live(transcript):
    counts = [int(value) for value in _COUNT.findall(transcript)]
    assert len(counts) >= 2, "the test runs your program twice and saw fewer than two counts"
    assert counts[-1] > counts[0], (
        f"the count did not grow between runs ({counts[0]} then {counts[-1]}). A constant is not "
        "a counter, and running a whole program in between costs many system calls."
    )


def test_the_worked_example_is_still_there():
    """Scaffolding: the problem points at an existing patch as the shape to copy."""
    patch = ROOT / "xv6" / "patches" / "06-trap-census.patch"
    assert patch.exists(), "the worked example this problem refers to has gone"
    assert "trapdump" in patch.read_text()
