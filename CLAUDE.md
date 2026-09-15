# CLAUDE.md

Project instructions for AI assistants working on this book. These are binding. §5 especially.

## What this is

*Systems From Scratch* — a self-study text on computer systems and performance, organised around
one question at every layer: **where do the cycles go, and how would I know?**

Read **PLAN.md** first: outline, settled decisions, conventions. Read **AUTHORING_GUIDE.md**
before writing or editing a chapter. `.claude/commands/chapter.md` is the per-chapter workflow.

## The three targets

Everything here follows from this, so do not work around it. `bench.outline.TARGET_MEANING` is
the source of truth; this is the prose version.

- **`bare`** — a RISC-V machine under `qemu-system-riscv64` with no kernel, no library and no
  loader. What the hardware itself does: reset, traps, privilege, page tables, harts. Part II
  builds each primitive on it before any kernel is read. **Never time anything here**, for
  exactly the reason `xv6` may not be timed.
- **`xv6`** — the MIT teaching kernel under `qemu-system-riscv64`. Structure and semantics.
  **Never time anything here.** QEMU models no cache, no branch predictor, no store buffer, no
  pipeline and no memory latency; a duration measured inside it describes the host machine and
  the translation strategy, not RISC-V.
- **`host`** — Linux on real hardware, natively, over SSH. Every number about cost. The reference
  machine is a Raspberry Pi 5; `hardware/README.md` says what any machine has to be able to do.

Three targets, but **two machines**: `bare` and `xv6` are both QEMU on whatever you are working
on, and share one cross compiler, so `scripts/verify-setup.py` checks their tooling once. Only
`host` has to be real hardware.

`bench.stamp.provenance_problems` enforces every direction and CI runs it. If you find yourself
wanting to relax it, the answer is no: an emulated timing is indistinguishable from a real one
once it is a number in a table, which is exactly why the check exists.

**The emulated targets and the real one do not share an instruction set, and that is
deliberate.** Part V needs `perf` to count *and* sample, and no purchasable RISC-V core does
both — staying on RISC-V would have made the whole-machine profiling chapter and the vectors
chapter unmeasurable. PLAN.md §5 and `hardware/README.md` carry the evidence. Do not "fix" the
inconsistency; it was bought with two chapters.

(Those two are named rather than numbered on purpose. This section said "ch27 and ch28" for a
while, off by one in both, because `scripts/sync-labels.py` does not scan this file — and could
not have fixed it anyway, since a bare `chNN` has no anchor to derive a number from. The rule in
*Chapter status* below applies to this file too: prefer the name.)

## Build

Jupyter Book 2, whose CLI is `mystmd`. Pinned in `package.json` (npm), **not** in
`requirements.txt` — one source of truth.

```bash
make check          # ./scripts/ci-check.sh — exactly what CI runs
make book           # live preview
make xv6-qemu       # boot the teaching kernel
make bench-listings # re-capture the disassembly the chapters quote
python3 scripts/verify-setup.py
```

## The four invariants

1. **No code pasted into prose.** `{literalinclude}` with `:start-at:` / `:end-before:` text
   anchors, never `:lines:`, pointing at real files. **Disassembly too** — it cannot be quoted
   from the tree because no compiler has run yet, so it is captured as a stamped `kind: listing`
   result (`bench/run_disasm.py`, `make bench-listings`) and rendered as a `Listing` figure.
   Unlike a timing, CI re-captures every listing on each push and fails if one instruction moved.
2. **No numbers typed into prose.** Every figure comes from a stamped JSON in `bench/results/`,
   declared in `bench/figures.py`, rendered to `chapters/_generated/` and `chapters/_figures/` by
   `scripts/render-figures.py`, and included. Chapters contain **no executable cells**. A cited
   specification is the one exception and needs `% number-ok: @citekey` on the preceding line.
3. **No invented figures.** A measurement that has not been taken is declared `pending=` and
   renders as a warning containing no numbers. Never a placeholder, never an estimate, never a
   number from a different machine.
4. **Problems are tests.** Each is a stub under `tests/<chapter-slug>/` with a test that passes only when
   solved, marked `problem` so CI deselects it. Never write the answer anywhere in the repository.

## 5. Originality — non-negotiable

This book covers ground that existing textbooks cover. It must be **entirely original work**.

- **Do not reproduce, closely paraphrase, or structurally mirror any existing book, lecture notes
  or course material.** Including, but not limited to: *Computer Systems: A Programmer's
  Perspective* (Bryant & O'Hallaron), the *xv6* book (Cox, Kaashoek, Morris), *Operating Systems:
  Three Easy Pieces*, *The RISC-V Reader*, *Performance Analysis and Tuning on Modern CPUs*,
  *Systems Performance*, *What Every Programmer Should Know About Memory*, and any C or algorithms
  textbook. Not their chapter structure, section headings, figures, example programs, problem
  sets, or characteristic phrasings.
- **If you notice you are reconstructing a known book's sequence, or a well-known example — a
  particular bomb-lab-style puzzle, a particular matrix-transpose figure, a particular problem
  numbering — stop and design a different one.** The feeling of "this is the standard way to
  present this" is the signal, not the permission.
- Ideas, facts, algorithms and public specifications are not copyrightable; **expression is**.
  Explain the same concepts with your own structure, your own examples, your own figures.
- **Source code.** xv6 is MIT: short excerpts with attribution are fine and encouraged, and this
  book's changes ship as patches under `xv6/patches/`, never as a copied tree. The RISC-V
  specifications are permissively licensed: cite them, redraw what is needed, never reproduce
  tables wholesale. Linux kernel excerpts are GPL: keep them very short, attributed, and prefer
  describing behaviour to quoting code. **Never reproduce code from a textbook.**
- **Citations.** Every factual claim about hardware behaviour cites either a measurement in
  `bench/results/` or a primary source in `references.bib` — a specification, a datasheet, a
  vendor manual, a paper. Textbooks may be cited as further reading in "Where to go next" and
  nowhere else; they are never a source for a chapter's content.
- **Maintain `ORIGINALITY.md`**: per chapter, the works closest to it in subject and one line on
  how this chapter's structure and examples differ. Update it in the **same commit** as the
  chapter. `tests/test_book.py` fails a finished chapter with no entry.
- The author will run a plagiarism check before publication. Write so it comes back clean.

## 6. Accuracy

- Every number in prose comes from a stamped result. No invented timings, and no "typically about
  a hundred cycles" without a measurement or a cited source.
- Every code example compiles and runs on its declared target in CI. Every `xv6` example is
  exercised under QEMU; every `host` example is cross-compiled for RV64 and run under user-mode
  QEMU for correctness. Timing runs happen in `make bench-board` on the board, and their results
  are committed.
- **When something cannot be measured on the available hardware** — no vector unit, no second
  board, a counter the firmware does not expose — the chapter says so in the text, shows the
  reasoning it used instead, and states what it would take to measure. It does not substitute a
  number from somewhere else.
- Prefer showing a measurement that surprises the reader to asserting a rule.
- Keep `ERRATA.md`. When a later chapter contradicts an earlier one, **fix the earlier one**.
- A specification is a claim about a product line; `/proc/cpuinfo` is a statement about the
  silicon that produced the number. Where they disagree, print the measurement and say so.

## 7. Voice

Direct, precise, British English, active voice, short sentences. First-person plural sparingly.
No marketing tone, no filler, no "in this chapter we will". Figures are drawn by code and must
show a mechanism.

**Length follows the material.** There is no page target, deliberately. A chapter is as long as
what it has to convey, and no longer — ch10 has a data model to take apart and ch28 has one
question about a vector unit, and forcing those to the same size would pad one and cramp the
other. A chapter is finished when PLAN.md §12.3 is satisfied, never when it reaches a number.

What that is not is licence to sprawl. The test is per section rather than per chapter: every
section earns its place or comes out, and the seven-part shape (PLAN.md §12.1) applies whatever
the length — a short chapter still owes the reader "What this cannot tell you".

## Things that will break the build

- **A timing recorded on the wrong target.** `verify-numbers.py` rejects it, correctly.
- **Editing `bench/measure.py`.** It is in `CORE_SOURCES`, so every committed result's fingerprint
  changes and `verify-numbers.py` fails until each is regenerated. Cheap for `xv6` results, and
  for `host` results it means going to the board. Treat it as frozen; ch21 adds the timing library
  to it once, deliberately.
- **Adding an executable cell to a chapter.** The book build is pure markdown and must stay that
  way — otherwise publishing a web page depends on a RISC-V toolchain.
- **Unpinned `mystmd`.** Always install the version from `package.json`.
- **Bare `pytest`.** Use `python3 -m pytest`, so tests run under the interpreter with the
  dependencies. A standalone pytest cannot import `bench`.
- **A test that reads `_build/`.** A local checkout has one; a CI runner does not. Such a test
  passes locally and fails in CI.
- **Modifying the xv6 submodule.** It must stay byte-identical to upstream; a test asserts it.
  Changes go in `xv6/patches/`, new programs in `xv6/apps/`, and everything is combined into
  `xv6/stage/` at build time.
- **A new MyST directive without a branch in `scripts/build-pdf.py`.** The renderer raises on a
  node type it does not handle, deliberately — the alternative is content silently missing from
  the PDF.
- **`BASE_URL`.** This is a project site at `/computer-systems/`. `deploy.yml` sets it from the
  Pages base path; without it every link 404s.

## Chapter status

All thirty chapters are written, and seven of the eight appendices. Appendix C waits for the
reference machine: which events a board exposes is a property of its silicon, kernel and firmware
together and cannot be drafted from a desk. Nineteen figures are `pending=` for the same reason —
they are `host` measurements and the board has not produced them yet. Regenerate a stub with
`python3 scripts/new-chapter.py --all --force`, which refuses to touch a written chapter.

**Five chapters depend on the reference machine** — ch22, ch24, ch25, ch27, ch28 — recorded as the
`assumes` field in `bench/outline.py`. That renders an **Assumes** row in the chapter header and
is required by `tests/test_book.py` to appear in ch00's list too. A chapter must not acquire a
hardware dependency without one.

**A chapter's number is never an identifier.** It used to be, and moving a chapter cost a rename
of every anchor, filename, test directory, checkpoint tag, figure id and permalink downstream of
it — three times, each one leaving prose whose text disagreed with the chapter it linked to, which
`--strict` cannot see because the anchor still resolves.

Identity is the slug: `(#virtual-memory)`, `chapters/virtual_memory.md`, `tests/virtual_memory/`,
`virtual-memory-walk`. The number survives only where a reader sees it — the heading, the sidebar
title, the text of a cross-reference — and is **derived**, by `scripts/sync-labels.py`, checked in
CI, exactly as every other number in this book is. Never type one into an identifier;
`tests/test_book.py` fails the attempt.

So inserting a chapter is now an edit to `bench/outline.py` and `myst.yml`, plus
`python3 scripts/sync-labels.py`. Nothing else moves.
