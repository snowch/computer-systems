"""Problem 1.1 — how long is each instruction?

A listing's left-hand column is an address counted from the start of the function, so the distance
to the next one is how many bytes the instruction took. RISC-V has short forms of its commonest
instructions and the compiler uses them without being asked, which is why this is a question at
all rather than a multiplication.

Fill in :func:`instruction_lengths`. Run:

    python3 -m pytest tests/reading_a_listing/test_problem_1_lengths.py
"""

from __future__ import annotations


def instruction_lengths(addresses: list[int], end: int) -> list[int]:
    """How many bytes each instruction occupies.

    :param addresses: each instruction's address, in order, counted from the function's start.
    :param end: the address one past the last instruction — where the next function begins.
    :returns: one length per address, in the same order.
    """
    raise NotImplementedError("Problem 1.1 — see the docstring above")
