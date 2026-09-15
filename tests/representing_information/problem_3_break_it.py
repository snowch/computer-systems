"""Problem 3 of chapter 2 — find the input that makes this wrong.

Here is a function that decides whether a read of `length` bytes starting at `start` stays inside
a buffer of `size` bytes. It is the shape of check that appears in real code, it looks correct,
and it is not.

    int fits(unsigned start, unsigned length, unsigned size) {
      return start + length <= size;
    }

Find one triple where it answers *yes* and the read would in fact run off the end. The test
performs the arithmetic in a width that cannot overflow, so it knows the true answer; your job is
to find where the function disagrees with it.

Chapter 2's section on arithmetic that is not arithmetic says what goes wrong. The type is
`unsigned`, so nothing here is undefined — the machine does exactly what it was told. That is the
uncomfortable part.
"""

from __future__ import annotations

#: The width the function's arguments have, which is the whole of the problem.
UNSIGNED_BITS = 32

#: Your counter-example: (start, length, size), all of which must fit in 32 bits.
COUNTER_EXAMPLE: tuple[int, int, int] | None = None
