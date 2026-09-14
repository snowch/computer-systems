"""Problem 0.1 — which of these numbers would you publish?

A result file carries where it was measured. Write the rule that decides whether a timing taken
under those conditions is one this book is allowed to print.

Run `python3 -m pytest tests/ch00/test_problem_1_trust.py` until it passes. The test will not
tell you the rule; chapter 0 does, and the result files under `bench/results/` are the shape you
are deciding about.
"""

from __future__ import annotations

from typing import Any


def can_you_publish_this_timing(result: dict[str, Any]) -> bool:
    """Return True only if a duration measured under these conditions means something.

    ``result`` is a stamped result payload — the same shape as any file in ``bench/results/``.
    The fields that matter are ``result["target"]`` and ``result["machine"]``; look at
    ``bench/stamp.py`` for what goes in them and what the values mean.
    """
    raise NotImplementedError("Problem 0.1 — see the Problems section of chapter 0.")
