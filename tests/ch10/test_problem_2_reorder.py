"""Checks Problem 2.2 by compiling the reader's ordering and asking the compiler how big it is.

The target to beat is computed, not stored: the test builds the arrangement that alignment theory
says is optimal, measures it, and requires the reader's to match. So a compiler with different
alignment rules moves the target rather than failing every reader.
"""

from __future__ import annotations

import pytest

from bench.measure import compile_program
from tests.ch10.problem_2_reorder import DECLARED, MEMBERS, ORDER

pytestmark = pytest.mark.hostcode

#: Alignment of each type, in bytes, under both of the book's ABIs. ch00 measured these rather
#: than assuming them, and the probe's table is where they come from.
_ALIGN = {"char": 1, "short": 2, "int": 4, "double": 8}


def _program(order) -> str:
    fields = "\n".join(f"  {MEMBERS[name]} {name};" for name in order)
    return f'#include <stdio.h>\nstruct s {{\n{fields}\n}};\nint main(void){{printf("%d\\n",(int)sizeof(struct s));return 0;}}\n'


def _sizeof(order, host_target, build_dir, stem: str) -> int:
    source = build_dir / f"reorder_{stem}.c"
    source.write_text(_program(order))
    built = compile_program([source], build_dir / f"reorder_{stem}", host_target)
    return int(built.run().stdout.strip())


@pytest.fixture(scope="module")
def best(host_target, build_dir) -> int:
    """Largest alignment first, which is the arrangement that leaves no interior padding."""
    order = sorted(MEMBERS, key=lambda name: -_ALIGN[MEMBERS[name]])
    return _sizeof(order, host_target, build_dir, "best")


@pytest.mark.problem
def test_the_reader_kept_every_member(best):
    assert ORDER, "Problem 2.2: ORDER is still empty"
    assert sorted(ORDER) == sorted(DECLARED), "same five members, reordered — none added or lost"


@pytest.mark.problem
def test_the_reader_ordering_wastes_nothing(host_target, build_dir, best):
    assert ORDER, "Problem 2.2: ORDER is still empty"
    measured = _sizeof(ORDER, host_target, build_dir, "reader")
    assert measured == best, (
        f"your ordering is {measured} bytes; these members fit in {best}. "
        "Every gap you are paying for is between two members whose order you chose."
    )


def test_the_declared_order_is_actually_worse(host_target, build_dir, best):
    """Scaffolding: if declaration order were already optimal there would be no problem here."""
    declared = _sizeof(DECLARED, host_target, build_dir, "declared")
    assert declared > best, (
        f"the declared order is {declared} bytes and the best is {best} — this problem has no "
        "signal on this ABI"
    )
