"""Problem 9.3 — which of these counts is a property of the workload?

Chapter 9 records two of the numbers the kernel's census prints and declines the rest. Decide for
yourself, before running anything, which is which.

For each counter below, set `True` if running the identical workload again must give the identical
number, and `False` if it need not. The workload is `intrload`, which writes a fixed number of
characters and performs a fixed number of block operations, and the boot is otherwise identical.

You are not being asked to guess what this book decided. You are being graded against what the
machine actually does: the test boots xv6 several times and compares the censuses, so a counter
you called reproducible had better come back the same every time.

    python3 -m pytest tests/ch16/test_problem_3_attribute.py

Think about what each interrupt *means* before you answer. Two of these are counting the same kind
of event and only one of them is countable, which is the chapter in one line.
"""

from __future__ import annotations

#: counter name -> True if a repeat run must produce the same number, False if it need not.
#: Replace each None with True or False.
ANSWER: dict[str, bool | None] = {
    # Interrupts, by source.
    "timer": None,
    "uart": None,
    "virtio": None,
    # What the console driver did with the characters.
    "chars_written": None,
    "write_sleeps": None,
    "rx_chars": None,
}
