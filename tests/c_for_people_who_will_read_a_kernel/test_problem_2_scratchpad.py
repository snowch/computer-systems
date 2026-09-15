"""Checks Problem 3.2 by running the program and reading what it printed.

One assertion, and it is the one the reader cannot satisfy by accident: both descriptions have to
survive to the `printf`. Storage duration is the subject — where a thing lives and how long it
stays there — and a fix that swaps one shared buffer for a different shared buffer fails here for
the same reason the original does.
"""

from __future__ import annotations

import pytest

from bench.measure import compile_program
from bench.stamp import ROOT

SOURCE = ROOT / "tests" / "c_for_people_who_will_read_a_kernel" / "scratchpad.c"

pytestmark = pytest.mark.hostcode


@pytest.fixture(scope="module")
def printed(host_target, build_dir) -> str:
    built = compile_program([SOURCE], build_dir / "scratchpad", host_target)
    return built.run().stdout.strip()


@pytest.mark.problem
def test_both_descriptions_survive(printed: str):
    assert printed == "negative positive", (
        f"the program printed {printed!r}. Both calls were asked for a different description and "
        "only one of them is there — where did the first one go?"
    )


def test_the_program_still_asks_for_two_different_things():
    """Scaffolding: the problem is only a problem while main() asks for two unlike answers."""
    source = SOURCE.read_text()
    assert "describe(-5)" in source and "describe(7)" in source, (
        "main() has been changed; the problem says not to"
    )
    assert source.count("printf") == 1, "main() should still print once, with both answers"
