"""Checks Problem 1.2. There is no answer key — this file is the answer key, and it runs."""

from __future__ import annotations

import pytest

from tests.setting_up_the_board.problem_2_sampling import parts_this_machine_can_finish

#: (description, can_count, can_sample, is_native, how far it gets)
CASES = [
    ("the reference board", True, True, True, "all"),
    ("counters but no sampling", True, False, True, "counting"),
    ("a laptop with QEMU and no board", False, False, False, "emulated"),
    ("a native machine whose counters are absent", False, False, True, "emulated"),
    ("sampling reported under emulation, which is a lie", True, True, False, "emulated"),
]


def test_emulation_overrides_everything_it_claims():
    """Scaffolding: the last case claims both capabilities and must still not reach Part V."""
    claimed = next(c for c in CASES if c[0].startswith("sampling reported"))
    assert claimed[1] and claimed[2] and not claimed[3]
    assert claimed[4] == "emulated", "a claim made under emulation is not a capability"


def test_counting_and_sampling_are_separate():
    """Scaffolding: two natives differing only in sampling must land differently."""
    both = next(c for c in CASES if c[1] and c[2] and c[3])
    counting = next(c for c in CASES if c[1] and not c[2] and c[3])
    assert both[4] != counting[4]


@pytest.mark.problem
@pytest.mark.parametrize(
    ("description", "count", "sample", "native", "expected"), CASES, ids=[c[0] for c in CASES]
)
def test_how_far_this_machine_gets(description, count, sample, native, expected):
    try:
        answer = parts_this_machine_can_finish(count, sample, native)
    except NotImplementedError:
        pytest.fail(
            "Problem 1.2 is not solved — see tests/setting_up_the_board/problem_2_sampling.py"
        )
    assert answer == expected, (
        f"{description}: you said {answer!r}, and the chapter says {expected!r}"
    )
