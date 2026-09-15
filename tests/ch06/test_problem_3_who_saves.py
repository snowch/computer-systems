"""Checks Problem 4.3 by reading the prologue and the body of a compiled function.

Two mechanical facts settle it: whether the register is written anywhere, and whether it is stored
to the stack in the prologue. The ABI class is not consulted to *grade* the answer — it is
consulted to check that the reader's two registers really do come from different halves of the
convention, which is the thing the problem is about.
"""

from __future__ import annotations

import re

import pytest

from bench.disasm import disassemble
from bench.run_disasm import target_for

#: A function that calls out and needs something afterwards, so it must use both kinds.
_SOURCE = """
long helper(long);
long reader_subject(const long *values, long count) {
  long total = 0;
  for (long i = 0; i < count; i++) {
    total += helper(values[i]) ^ i;
  }
  return total;
}
"""

#: The two halves of the RISC-V convention @riscv-psabi, by name. Which half a register is in is
#: the whole of what this problem is about, so the split is stated rather than derived.
CALLER_SAVED = {"ra", *(f"t{n}" for n in range(7)), *(f"a{n}" for n in range(8))}
CALLEE_SAVED = {"sp", "gp", "tp", *(f"s{n}" for n in range(12))}

_WRITE = re.compile(r":\t\S+\s+(\w+),")
_SAVE = re.compile(r"\bsd\s+(\w+),-?\d+\(sp\)")


@pytest.fixture(scope="module")
def compiled(tmp_path_factory) -> tuple[set[str], set[str]]:
    """(registers written anywhere, registers stored to the stack)."""
    directory = tmp_path_factory.mktemp("whosaves")
    (directory / "subject.c").write_text(_SOURCE)
    text = disassemble(
        [str(directory / "subject.c")],
        "reader_subject",
        target_for("riscv64"),
        includes=[],
        build_dir=directory,
    ).text
    return set(_WRITE.findall(text)), set(_SAVE.findall(text))


@pytest.mark.problem
def test_the_freely_used_register_is_never_saved(compiled):
    from tests.ch06.problem_3_who_saves import USED_FREELY  # noqa: PLC0415

    written, saved = compiled
    assert USED_FREELY is not None, "Problem 4.3: USED_FREELY is still None"
    assert USED_FREELY in written, f"{USED_FREELY} is not written by this function at all"
    assert USED_FREELY not in saved, f"{USED_FREELY} *is* saved to the stack here"
    assert USED_FREELY in CALLER_SAVED, (
        f"{USED_FREELY} is callee-saved, so a function that writes it without saving it would be "
        "breaking the convention rather than using it"
    )


@pytest.mark.problem
def test_the_saved_register_had_to_be(compiled):
    from tests.ch06.problem_3_who_saves import SAVED_FIRST  # noqa: PLC0415

    written, saved = compiled
    assert SAVED_FIRST is not None, "Problem 4.3: SAVED_FIRST is still None"
    assert SAVED_FIRST in saved, f"{SAVED_FIRST} is not stored to the stack by this function"
    assert SAVED_FIRST in CALLEE_SAVED or SAVED_FIRST == "ra", (
        f"{SAVED_FIRST} is caller-saved, so saving it would be this function doing somebody "
        "else's job"
    )


def test_the_function_uses_both_kinds(compiled):
    """Scaffolding: the problem needs a function that genuinely has to do both."""
    written, saved = compiled
    assert written & CALLER_SAVED, "nothing caller-saved is written — wrong subject function"
    assert saved, "nothing is saved — this function has no prologue to read"
