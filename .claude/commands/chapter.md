---
description: Write a chapter of Systems From Scratch, end to end
---

Write chapter $ARGUMENTS of *Systems From Scratch*.

Before writing anything, read `CLAUDE.md`, `PLAN.md`, `AUTHORING_GUIDE.md`, `ORIGINALITY.md` and
the previous chapter. Then:

1. **Write the problems and their tests first**, under `tests/chNN/`, and make sure each one
   fails for the right reason. A problem whose test passes before it is solved is not a problem.
   Mark the reader's assertions `@pytest.mark.problem`; leave the scaffolding tests unmarked so
   CI keeps checking that the problem is answerable.
2. **Write the companion code** into `sysfs/` (host) or `xv6/apps/` and `xv6/patches/` (xv6).
   It must compile and run on its declared target in CI.
3. **Declare the figures** in `bench/figures.py` and write the runner that produces them under
   `bench/run_*.py`. For a `host` figure that needs the board, declare it `pending=` — never a
   placeholder number — and write the prose so it reads correctly once the measurement lands.
4. **Write the chapter** to serve the problems and the measurements, in the seven-part shape.
   Quote code with `{literalinclude}` and text anchors; include figures with `{include}`. No
   number is ever typed into prose.
5. **Update `ORIGINALITY.md`** for this chapter, in this commit. Obey CLAUDE.md §5 absolutely.
6. Run `./scripts/ci-check.sh`, then `python3 scripts/build-pdf.py`, then commit and tag with
   this chapter's tag from `CHECKPOINTS.md`.

Stop and report what was measured, what is still pending on the board, and what the chapter says
it could not measure.
