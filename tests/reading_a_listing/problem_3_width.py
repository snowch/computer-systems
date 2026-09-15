"""Problem 1.3 — how wide was the element?

A pointer step is not one byte; it is one *element*, and the compiler turns the element into a
byte count before the instruction is emitted. Given the instruction, the byte count is visible and
the element width can be recovered from it.

Fill in :func:`element_width`. Run:

    python3 -m pytest tests/reading_a_listing/test_problem_3_width.py
"""

from __future__ import annotations


def element_width(offset: int, steps: int) -> int:
    """How many bytes wide one element is.

    :param offset: the byte offset the instruction carries, e.g. the ``4`` in ``lw a0,4(a0)``.
    :param steps: how many elements past the pointer the source asked for — ``p + 1`` is 1.
    """
    raise NotImplementedError("Problem 1.3 — see the docstring above")
