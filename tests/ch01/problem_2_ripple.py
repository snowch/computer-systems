"""Problem 2 of chapter 1 — predict what a source change disturbs.

Change one line of a program and something downstream changes. Which stages notice?

For each change below, say whether the file that stage produced comes out different. Then run
`python3 -m pytest tests/ch01/test_problem_2_ripple.py`, which does not compare your answer with
a stored one: it makes the change, runs the toolchain, and compares the files.

That is the point of the exercise. You are not being marked against an answer key — you are
being marked against a compiler, and when you disagree with it, it is right and the interesting
question is why.
"""

from __future__ import annotations

#: The stages, as `sysfs/tools/stages.sh` names them.
STAGES = ("preprocess", "compile", "assemble", "link")


def stages_disturbed_by(change: str) -> set[str]:
    """Return the stages whose output differs after ``change``.

    ``change`` is one of the keys in ``CHANGES`` below. Return a set drawn from :data:`STAGES` —
    empty if nothing downstream can tell the difference at all.
    """
    raise NotImplementedError("Problem 1.2 — see the Problems section of chapter 1.")


#: The edits, each described exactly as the test will perform it on a copy of the program.
CHANGES = {
    "add_a_comment": "add a line of comment above main()",
    "rename_a_local": "rename the loop counter in both summing functions from n to index",
    "change_the_span": "change SYSFS_STAGES_SPAN from 64 to 65",
    "add_an_uncalled_static": "add a static function nothing calls",
}
