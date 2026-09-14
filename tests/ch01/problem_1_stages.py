"""Problem 1.1 — which stage produced this?

Four programs run when you type one command, and each leaves a file behind. Given a fragment of
one of those files, say which stage wrote it.

Run `python3 -m pytest tests/ch01/test_problem_1_stages.py` until it passes. The fragments in the
test are real: they come from walking `sysfs/tools/sameanswer.c` through the toolchain, which you
can do yourself with `sysfs/tools/stages.sh`. Looking at your own output is a better way to solve
this than guessing from the shapes.
"""

from __future__ import annotations


def which_stage_wrote_this(fragment: str) -> str:
    """Return the stage that produced ``fragment``.

    One of ``"preprocess"``, ``"compile"``, ``"assemble"`` or ``"link"`` — the four stages
    chapter 1 walks through, named as `stages.sh` names them.

    ``fragment`` is a few lines lifted out of one of the four files. Think about what each stage
    is allowed to know: the preprocessor has never heard of a function, the compiler has never
    heard of an address, and the assembler knows the addresses inside one file and no others.
    """
    raise NotImplementedError("Problem 1.1 — see the Problems section of chapter 1.")
