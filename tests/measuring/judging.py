"""Problems 24.5 to 24.7 — judging a measurement rather than taking one.

Three functions to write. None of them measures anything: they decide what a measurement is
allowed to claim, which is the half of the chapter that survives a change of machine.

Nothing in `bench/` answers these for you. `bench.distribution` computes intervals and applies
the rule; what it does not do is say which *kind* of undecided answer you have, which timings are
reportable at all, or what a stamp still owes. Those are the reader's, and the tests check them
against definitions they compute rather than against a stored key.
"""

from __future__ import annotations

from typing import Any, Literal

#: Why a comparison declined to call a winner.
#:
#: The two are not interchangeable, and telling them apart decides what you do next: one says
#: gather more evidence, the other says stop measuring and go and do something else.
Reason = Literal["no evidence", "too small to matter"]


def why_undecided(decision: dict[str, Any]) -> Reason:
    """Which kind of "cannot tell" is this?

    ``decision`` is what :func:`bench.distribution.decide` returned, and its verdict is
    "cannot tell". Two quite different situations produce that:

    * the interval on the difference **contains zero**, so this run is consistent with the two
      being identical. More runs might settle it;
    * the interval **excludes** zero — there really is a difference — but the difference is under
      the threshold that was fixed in advance. More runs will not help, because the answer is
      already known and it is "yes, and nobody cares".

    Return which one. The fields you need are all in ``decision``; problem 24.5 is noticing which.
    """
    raise NotImplementedError("problem 24.5")


def reportable(measured_ns: float, timer_overhead_ns: float, *, factor: float = 100.0) -> bool:
    """May this timing be published?

    A measured region has to be enough larger than the instrument that measured it for the
    instrument not to be most of the answer. ``factor`` is how many times larger this book
    requires, and the chapter derives it.

    Return True only when the measurement clears that bar. A region *shorter* than the timer
    overhead is the case to get right: it is not a fast measurement, it is not a measurement, and
    a harness that reports one is reporting its own clock.
    """
    raise NotImplementedError("problem 24.6")


def environment_record(readings: dict[str, Any]) -> dict[str, Any]:
    """Complete the environment a stamp has to carry.

    ``readings`` is what the machine managed to answer — some fields present, some missing
    entirely because this board has no sensor for them. Return a record containing **every** field
    the chapter argued for, with ``None`` where the machine could not say.

    The distinction the test checks is the one the chapter makes: an absent key means the harness
    never looked, and a null means it looked and the machine declined. They are different claims
    and a stamp that conflates them cannot be judged later.

    :data:`bench.distribution.REQUIRED_ENVIRONMENT` is the list of fields. Using it is expected;
    the problem is what to do about the ones that are not in ``readings``.
    """
    raise NotImplementedError("problem 24.7")
