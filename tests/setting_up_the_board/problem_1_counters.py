"""Problem 1.1 — is this counter real?

`perf stat` will print a number whether or not the hardware produced one. A counter can be
missing, emulated by the kernel, or multiplexed across too few hardware slots, and each of those
reaches you as a figure that looks exactly like a count.

Fill in :func:`counts_hardware_events`. Run:

    python3 -m pytest tests/setting_up_the_board/test_problem_1_counters.py
"""

from __future__ import annotations


def counts_hardware_events(report: dict) -> bool:
    """True if this `perf stat` outcome is a count of something the hardware did.

    :param report: one event's outcome, with keys ``value`` (the number printed, or None),
        ``supported`` (did the kernel claim the event exists), ``emulated`` (did the kernel
        compute it rather than read it) and ``multiplexed`` (was it time-shared with others).
    """
    raise NotImplementedError("Problem 1.1 — see the docstring above")
