"""Problem 1.2 — the three routines the kernel writes for itself.

Every key is computed by the test from the same bytes the program is given, so nothing is stored.
The copy is checked against a sum the harness takes itself rather than through the reader's own
compare, because checking one unsolved function with another lets two wrong answers agree.
"""

from __future__ import annotations

import pytest

from tests.reading_c.harness import ask, checksum

STRINGS = ["", "a", "hello", "kernel/string.c", "x" * 60]

# (n, text) — copy the first n bytes of text.
COPIES = [(0, "abcdef"), (1, "abcdef"), (6, "abcdef"), (15, "kernel/string.c")]

# (a, b, n)
COMPARISONS = [
    ("abc", "abc", 3),
    ("abc", "abd", 3),
    ("abd", "abc", 3),
    ("abc", "abd", 2),
    ("abc", "abc", 0),
    ("\x01", "\x7f", 1),
]

SENTINEL = ord(".")


def expected_compare(a: str, b: str, n: int) -> int:
    # Not strict: the two may be different lengths, and comparing only the first n bytes of
    # each is the point — memcmp does not care what follows them.
    for x, y in zip(a.encode()[:n], b.encode()[:n], strict=False):
        if x != y:
            return x - y
    return 0


def test_comparing_zero_bytes_finds_no_difference():
    """Scaffolding: the boundary that a loop written the obvious way gets right by accident."""
    assert expected_compare("abc", "zzz", 0) == 0


def test_the_comparison_is_signed_and_ordered():
    """Scaffolding: returning 1 or -1 is a different function, and swapping the arguments must
    swap the sign."""
    assert expected_compare("abc", "abd", 3) == -1
    assert expected_compare("abd", "abc", 3) == 1
    assert expected_compare("abc", "abd", 2) == 0


@pytest.mark.problem
def test_length_stops_at_the_terminator(declarations):
    answered = ask(declarations, [f"l{text}" for text in STRINGS])
    wrong = {
        text: {"expected": len(text), "got": answered["length"][i]}
        for i, text in enumerate(STRINGS)
        if answered["length"][i] != len(text)
    }
    assert not wrong, f"the bytes before the zero, and not the zero: {wrong}"


@pytest.mark.problem
def test_copy_moves_exactly_n_bytes_and_not_one_more(declarations):
    answered = ask(declarations, [f"c{n}:{text}" for n, text in COPIES])
    wrong = {}
    for index, (n, text) in enumerate(COPIES):
        want = (checksum(text.encode()[:n]), SENTINEL)
        if answered["copy"][index] != want:
            wrong[f"{n} of {text!r}"] = {"expected": want, "got": answered["copy"][index]}
    assert not wrong, (
        f"the second number is the byte just past the copy, which must still be untouched: {wrong}"
    )


@pytest.mark.problem
def test_compare_returns_the_difference_rather_than_a_flag(declarations):
    answered = ask(declarations, [f"m{a},{b},{n}" for a, b, n in COMPARISONS])
    wrong = {
        f"{a!r} vs {b!r} over {n}": {
            "expected": expected_compare(a, b, n),
            "got": answered["compare"][i],
        }
        for i, (a, b, n) in enumerate(COMPARISONS)
        if answered["compare"][i] != expected_compare(a, b, n)
    }
    assert not wrong, f"first differing pair, as unsigned char, first minus second: {wrong}"
