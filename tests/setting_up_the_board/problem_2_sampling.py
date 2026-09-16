"""Problem 1.2 — can this machine sample?

Counting and sampling are separate capabilities. Counting needs a counter; sampling needs the
counter to raise an interrupt when it overflows, which is a different piece of hardware and is
optional on some architectures. A machine can do the first perfectly and not the second at all.

Fill in :func:`parts_this_machine_can_finish`. Run:

    python3 -m pytest tests/setting_up_the_board/test_problem_2_sampling.py
"""

from __future__ import annotations


def parts_this_machine_can_finish(can_count: bool, can_sample: bool, is_native: bool) -> str:
    """How far through the book this machine gets.

    :param can_count: `perf stat` reads real hardware counters.
    :param can_sample: `perf record` collects samples.
    :param is_native: the code runs on the hardware rather than under emulation.
    :returns: one of ``"none"``, ``"emulated"`` (everything before Part V), ``"counting"``
        (Part V except the chapters that need a profiler) or ``"all"``.
    """
    raise NotImplementedError("Problem 1.2 — see the docstring above")
