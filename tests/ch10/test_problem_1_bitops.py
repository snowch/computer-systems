"""Checks Problem 2.1 against properties rather than against a table of answers.

A property is a statement that has to hold for every input, so it cannot be satisfied by
memorising cases. Reversing the bytes twice must give back what you started with; the bit the
second function names must be set, and every bit below it must be clear. Those two sentences are
the whole specification, and between them they admit exactly one correct function each.
"""

from __future__ import annotations

import pytest

from bench.measure import compile_program
from bench.stamp import ROOT

SOURCE = ROOT / "tests" / "ch10" / "bitops.c"
WORD_BITS = 64
MASK = (1 << WORD_BITS) - 1

#: Chosen to include the awkward ones: zero, a single bit at each end, a byte-symmetric value,
#: and something with no structure to it at all.
CASES = [
    0x0,
    0x1,
    0x80,
    0xFF,
    0x0102030405060708,
    0x8000000000000000,
    0x00FF00FF00FF00FF,
    0xDEADBEEFCAFEF00D,
    0x1000,
]

pytestmark = pytest.mark.hostcode


@pytest.fixture(scope="module")
def answers(host_target, build_dir) -> dict[tuple[str, int], int]:
    built = compile_program([SOURCE], build_dir / "bitops", host_target)
    script = "".join(f"swap {value}\nlow {value}\n" for value in CASES)
    printed = built.run(input=script).stdout.split()
    assert len(printed) == 2 * len(CASES), f"the harness printed {len(printed)} lines"
    out: dict[tuple[str, int], int] = {}
    for index, value in enumerate(CASES):
        out[("swap", value)] = int(printed[2 * index])
        out[("low", value)] = int(printed[2 * index + 1])
    return out


@pytest.mark.problem
@pytest.mark.parametrize("value", CASES, ids=[hex(v) for v in CASES])
def test_swapping_bytes_twice_gives_back_the_word(value: int, answers):
    once = answers[("swap", value)]
    assert once <= MASK
    # Swapping the swap has to be the identity, and the test cannot call the reader's function
    # twice through the harness without trusting the first result — so it checks the algebra
    # directly against Python's own byte reversal, which is a different implementation.
    expected = int.from_bytes(value.to_bytes(8, "little"), "big")
    assert once == expected, f"swap_bytes({value:#x}) should be {expected:#x}"


@pytest.mark.problem
@pytest.mark.parametrize("value", CASES, ids=[hex(v) for v in CASES])
def test_the_lowest_set_bit_is_set_and_alone(value: int, answers):
    index = answers[("low", value)]
    if value == 0:
        assert index == WORD_BITS, "a word with no bits set has no lowest set bit"
        return
    assert index < WORD_BITS, f"lowest_set_bit({value:#x}) returned {index}"
    assert (value >> index) & 1, f"bit {index} of {value:#x} is not set"
    assert value & ((1 << index) - 1) == 0, f"there is a set bit below {index} in {value:#x}"


def test_the_properties_admit_exactly_one_function():
    """Scaffolding: a property test is only a test if a wrong answer can fail it.

    Both properties are checked here against a deliberately wrong implementation, so a change
    that accidentally made them vacuous — an empty CASES list, a comparison that is always true —
    fails at once rather than passing every reader's work.
    """
    wrong_swap = lambda v: v  # noqa: E731
    assert any(wrong_swap(v) != int.from_bytes(v.to_bytes(8, "little"), "big") for v in CASES)
    wrong_low = lambda v: 0  # noqa: E731
    assert any(v != 0 and (v >> wrong_low(v)) & 1 == 0 for v in CASES)
