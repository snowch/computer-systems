"""Problem 1.2 — does this operand touch memory?

Parentheses mean memory on RISC-V and square brackets mean it on AArch64. Everything else in an
operand position is a register or a literal, however much it looks like arithmetic.

Fill in :func:`reaches_memory`. Run:

    python3 -m pytest tests/reading_a_listing/test_problem_2_memory.py
"""

from __future__ import annotations


def reaches_memory(operand: str) -> bool:
    """True if reading this operand means going to memory, False if it names a register or literal.

    :param operand: one operand, exactly as a listing prints it — ``a0``, ``4(a0)``, ``[x2, #8]``.
    """
    raise NotImplementedError("Problem 1.2 — see the docstring above")
