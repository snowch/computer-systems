"""Checks Problem 3.3 by building the reader's table into a real C program and calling through it.

The table is generated from the reader's answer rather than written by them, because the exercise
is choosing what goes in each slot and knowing what the declaration has to say — not retyping an
array initialiser. The test writes the declaration and the reader supplies its contents.
"""

from __future__ import annotations

import pytest

from bench.measure import compile_program
from bench.stamp import ROOT
from tests.c_for_people_who_will_read_a_kernel.problem_3_dispatch import ORDER, TABLE

DEVICES = ROOT / "tests" / "c_for_people_who_will_read_a_kernel" / "devices.c"

#: What each slot must do, checked by calling it. Written as the *behaviour* wanted rather than
#: the function name, so the answer is not sitting here next to the question.
EXPECTED = {
    "reset": (0, 4),  # put it back to a known state: it clears four registers
    "read": (7, 107),  # fetch what it holds: the value plus its port
    "write": (300, 2),  # accept a value: a big one takes two bytes
    "status": (0xE, 0x2),  # report the flags: the low two bits of the argument
}

pytestmark = pytest.mark.hostcode


@pytest.fixture(scope="module")
def dispatched(host_target, build_dir):
    if not TABLE:
        pytest.fail("Problem 3.3: TABLE is still empty")
    missing = set(ORDER) - set(TABLE)
    assert not missing, f"no function chosen for {sorted(missing)}"

    slots = ", ".join(TABLE[name] for name in ORDER)
    declarations = "\n".join(f"int {fn}(int);" for fn in sorted(set(TABLE.values())))
    main = build_dir / "dispatch_main.c"
    main.write_text(
        f"#include <stdio.h>\n{declarations}\n"
        f"static int (*ops[{len(ORDER)}])(int) = {{ {slots} }};\n"
        'int main(void){ int a[4]; for (int i=0;i<4;i++) if (scanf("%d", &a[i])!=1) return 1;\n'
        f'  for (int i=0;i<{len(ORDER)};i++) printf("%d\\n", ops[i](a[i])); return 0; }}\n'
    )
    built = compile_program([main, DEVICES], build_dir / "dispatch", host_target)
    script = "\n".join(str(EXPECTED[name][0]) for name in ORDER) + "\n"
    printed = built.run(input=script).stdout.split()
    return dict(zip(ORDER, (int(v) for v in printed), strict=True))


@pytest.mark.problem
@pytest.mark.parametrize("operation", ORDER)
def test_each_slot_does_its_job(operation: str, dispatched):
    argument, want = EXPECTED[operation]
    assert dispatched[operation] == want, (
        f"slot {operation!r} given {argument} returned {dispatched[operation]}, wanted {want}. "
        "Read what the functions in devices.c do rather than what they are called."
    )


def test_the_names_do_not_give_it_away():
    """Scaffolding: one function's name must not match the slot it belongs in.

    A table anybody can fill in by matching strings teaches nothing about dispatch, so this
    guards the one thing that makes the problem worth setting.
    """
    source = DEVICES.read_text()
    assert "device_reset_flags" in source and "does not reset" in source
