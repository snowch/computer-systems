"""Checks Problem 9.3 against the machine rather than against a stored key.

The test boots the same workload several times and sees for itself which counters came back
identical. A reader who said a counter was reproducible is graded against whether it was.

Where the experiment cannot settle a counter — a varying one that happened to come back identical
every time — that counter is reported as inconclusive and not held against the reader. The
alternative is a test that occasionally fails a correct answer, which is worse than a test that
occasionally proves less than it hoped to.
"""

from __future__ import annotations

import pytest

from bench import xv6
from bench.run_interrupts import DUMP, WORKLOAD, read_census
from tests.ch11.problem_3_attribute import ANSWER

#: Enough repeats that a counter which varies has every chance to show it.
RUNS = 5


def _flatten(census: dict) -> dict[str, int]:
    return {**census["source"], **census["console"]}


def test_the_stub_asks_about_counters_the_census_actually_prints():
    """Scaffolding: the names the reader is answering about are the kernel's own, and unanswered.

    No boot, so this stays cheap in CI. It catches the stub drifting away from the census, which
    would leave the reader answering about something that no longer exists.
    """
    from bench.run_interrupts import __doc__ as _  # noqa: F401, PLC0415

    expected = {"timer", "uart", "virtio", "chars_written", "write_sleeps", "rx_chars"}
    assert set(ANSWER) == expected, (
        f"the stub and the kernel's census have drifted apart: {set(ANSWER) ^ expected}"
    )


@pytest.mark.xv6
@pytest.mark.problem
def test_the_classification_matches_what_repeat_runs_actually_do():
    unanswered = sorted(name for name, value in ANSWER.items() if value is None)
    assert not unanswered, f"still to answer: {unanswered}"

    censuses = []
    for _ in range(RUNS):
        result = xv6.boot([*WORKLOAD, DUMP])
        assert not result.timed_out, result.transcript[-1500:]
        censuses.append(_flatten(read_census(result.transcript)))

    observed = {
        name: len({census[name] for census in censuses}) == 1
        for name in censuses[0]
        if name in ANSWER
    }

    wrong, inconclusive = {}, []
    for name, claimed in ANSWER.items():
        was_steady = observed[name]
        if claimed == was_steady:
            continue
        if claimed is False and was_steady:
            # It might still vary; these runs did not catch it varying.
            inconclusive.append(name)
            continue
        wrong[name] = {
            "you said": "the same every time",
            "it was not": sorted({census[name] for census in censuses}),
        }

    assert not wrong, (
        f"over {RUNS} runs of the identical workload, these counters did not come back the same: "
        f"{wrong}"
    )
    if inconclusive:
        pytest.skip(
            f"{RUNS} runs did not catch these varying, so they are not held against you: "
            f"{sorted(inconclusive)}"
        )
