"""Checks Problem 4.3 by building and booting whatever the reader wrote.

Same compiler, same flags, same linker script as the chapter's own programs, so the machine the
answer runs on is the machine the chapter describes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench import bare

ANSWER = Path(__file__).parent / "answer.c"


def test_the_chapters_own_program_still_builds_and_runs():
    """Scaffolding: the harness this problem depends on works, before blaming the reader."""
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert bare.run("trap").fields()["register_survived"] == 1


@pytest.mark.problem
def test_the_readers_handler_saves_the_register_itself(tmp_path):
    if bare.problems():
        pytest.skip("; ".join(bare.problems()))
    assert ANSWER.exists(), f"Problem 4.3: write your program in {ANSWER.name} beside this test"

    source = ANSWER.read_text()
    assert "interrupt(" not in source, (
        "the point of the problem is to do without the attribute; it is still in your program"
    )
    assert "mret" in source, "something has to return from the trap, and `ret` will not do it"

    image = bare.build_from([ANSWER], "problem_by_hand", build_dir=tmp_path)
    run = bare.run("trap", image=image, timeout=30)
    assert run.fields().get("register_survived") == 1, (
        "the program ran, but the register the handler was supposed to preserve did not survive"
    )
