# Authoring Guide

How to write a chapter of *Systems From Scratch* without breaking the three things that make the
book worth reading: measured numbers, code that matches the prose, and problems that cannot lie
about whether you solved them.

## Quick start

```bash
npm install -g "mystmd@$(node -p "require('./package.json').devDependencies.mystmd")"
python3 -m pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
git submodule update --init --recursive

python3 scripts/verify-setup.py    # which targets this machine can run
make book                          # live preview at localhost:3000
make check                         # exactly what CI runs
```

`python3 -m pip`, not a standalone tool install: `python3 -m pytest` has to work, and a pipx or
uv `pytest` has its own environment and cannot import `bench`.

## The order to write in

Not the order the chapter is read in.

1. **The problems, and their tests.** Before any prose. Make each one fail, and read the failure
   — it is the first thing a reader will see, and it should tell them what to do rather than what
   went wrong. Mark the reader's assertions `@pytest.mark.problem`.
2. **The scaffolding tests.** Unmarked, beside the problems: the C compiles, the kernel boots with
   the stub staged, the harness produces output. CI runs these and deselects the problems. The
   book is responsible for handing the reader a problem that works.
3. **The companion code.** Into `sysfs/` for the `host` target, `xv6/apps/` and `xv6/patches/` for
   `xv6`. It must build and run on its declared target in CI.
4. **The runner and the figures.** A `bench/run_*.py` that produces stamped results, and an entry
   per figure in `bench/figures.py`.
5. **The chapter**, to serve all of the above.
6. **`ORIGINALITY.md`**, in the same commit.

Writing the prose first produces a chapter that explains what you meant to measure.

## The seven-part shape

PLAN.md §12.1, and it is not negotiable — the repetition is what makes twenty-two chapters read as
one book. `python3 scripts/new-chapter.py NN` generates the shape with the chapter's target,
question and prerequisites already filled in from `bench/outline.py`.

The section that matters most is the fifth: **What this cannot tell you**. It is the easiest to
skip and the one that makes the other six believable. If a chapter genuinely has no limits worth
naming, the chapter is not finished — go and look harder at the measurement.

## Five rules that are not negotiable

### Never paste code into prose

Quote it from the working tree, so it cannot drift:

````markdown
```{literalinclude} ../sysfs/lib/bits.c
:language: c
:start-at: uint64_t sysfs_reverse_bits
:end-before: uint64_t sysfs_popcount
```
````

Anchor on `:start-at:` / `:end-before:` **text**, never `:lines:` — line numbers rot on the first
edit above them, and `tests/test_book.py` fails a chapter that uses them.

**Machine code is not an exception, it just has its own mechanism.** A disassembly listing cannot
be quoted from the tree, because it does not exist there until a compiler runs — so it is captured
as a stamped result instead, exactly like a measurement:

1. put the function in a real source file (`sysfs/lib/shapes.c` is the one ch00 uses);
2. add its name to `SYMBOLS` in `bench/run_disasm.py`;
3. `make bench-listings` to capture it and commit the result;
4. declare a `Listing` figure in `bench/figures.py` naming the symbol and the results to show;
5. `make figures`, and `{include}` the fragment.

The listing then carries the compiler, its flags and the exact `objdump` command that produced it,
and CI re-captures it on every push and fails if a single instruction has changed. Never paste
objdump output into a chapter: it looks authoritative, nobody can check it, and it stops being
true the first time the toolchain moves.

### Never type a number into prose

Numbers come from `bench/results/*.json`. Declare the figure in `bench/figures.py`, render it, and
include the fragment:

```bash
python3 scripts/render-figures.py            # write the fragments and diagrams
python3 scripts/render-figures.py --check     # fail if a committed one is stale
```

````markdown
```{include} _generated/ch17-cache-latency.md
```
````

`scripts/verify-numbers.py` scans chapter prose for figures carrying a cost unit and fails the
build. If the number is a cited *specification* rather than a measurement — a clock rate from a
datasheet — put `% number-ok: @citekey` on the line before it, so the exemption and its reason are
visible in review.

### Say which earlier chapter your Part IV chapter costs

Part IV is not a second book. It is Part III's chapters asked again as questions about time, and
the thing that keeps it feeling that way is the `answers` field in `bench/outline.py`: the earlier
chapters whose cost this one measures. It renders as an **Answers the cost of** row in the header,
and `tests/test_book.py` checks the labels are real, point backwards, and appear in the header.

Write the chapter to earn that row. Open by recalling the mechanism the reader already has, then
put a price on it. Where the two targets disagree about more than the number — different
instruction set, different memory model — say so and draw the correspondence explicitly. The
correspondence *is* the content; a chapter that quietly pretends both halves are the same
architecture is worse than one that makes the translation.

Three Part IV chapters have no counterpart by design (ch16, ch22, ch23). Any other unpaired one
fails a test, because it is far more likely to be an oversight than a decision.

### Never let a chapter depend on the reference hardware silently

Readers are told to buy a board meeting a capability spec, not a part number (`hardware/`), so
theirs will differ from the machine the committed figures came from. Most chapters do not care.
If yours does — it assumes a cache shape, a core count, an in-order pipeline, the presence or
absence of an extension — record it as that chapter's `assumes` field in `bench/outline.py`.

That one edit puts an **Assumes** row in the chapter header and makes `tests/test_book.py` insist
the chapter also appears in ch00's list of hardware-sensitive chapters. Prose saying the same
thing gets dropped the first time the chapter is rewritten; data does not.

State what *changes* on other hardware, not merely that something does. "Assumes four cores" is a
warning. "A different core count moves the scaling curve without changing the mechanism" is
useful.

### Never let a target answer the other one's question

The `xv6` target produces no timings, ever. `bench.stamp.provenance_problems` rejects an `xv6`
result whose summary contains anything durational, and rejects a `host` result that was not
measured natively on the board. If you find yourself wanting a rough idea of how long something
takes under QEMU: that number describes the laptop QEMU is running on.

### Never invent a figure you have not measured

For a `host` figure that needs the board, declare it `pending=` with the command that produces it:

```python
"ch17-cache-latency": Table(
    render=tables.latency_table,
    result="cache-latency",
    pending=f"Cache latencies are not measured yet: {BOARD} (`bench/results/cache-latency.json`).",
),
```

It renders as a warning box containing no numbers at all, and **you write the prose around it as
though the numbers were there**, so that landing them is a one-command change and not a rewrite.
When the measurement arrives, remove the marker in the same commit —
`scripts/verify-numbers.py` fails if a pending figure's result file exists.

## Measuring

```bash
make bench-xv6      # every xv6-target result. Runs anywhere QEMU does.
make bench-board    # every host-target result. ON THE BOARD ONLY — it refuses elsewhere.
make figures        # re-render everything from committed results
```

A runner's job is to produce a summary and hand it to `bench.stamp.build_result` with the sources
it depends on. Record raw samples in the result where they are small enough to be useful: a
distribution someone can re-examine is worth far more than a summary they have to trust.

`CORE_SOURCES` in `bench/stamp.py` invalidates **every** result when it changes. Treat it as
frozen. ch16 adds the timing library to it once, deliberately.

## Problems

A problem is a stub the reader edits and a test that passes only when they are right.

- Put the stub and its test in `tests/chNN/`. The stub's docstring is the problem statement; the
  chapter's Problems section is the invitation.
- Make failure messages teach. `assert measured == expected` tells a reader nothing; "the padding
  between two members is whatever it takes to satisfy the alignment of the one that comes second"
  tells them where to look.
- An xv6 problem's answer lives under `tests/`, not in `xv6/apps/`, and is staged with
  `xv6.boot(..., extra_apps=[...])`. A program that does not compile should fail the reader's
  test, not everybody's kernel build.
- Never write the answer anywhere in the repository. The test is the answer key, and it runs.

## Cross-references and citations

Chapters carry a label matching their number, so refer to them as `[ch10](#ch10)` and to
appendices as `[Appendix B](#appendix-b)`. MyST resolves these at build time and the build fails on
a broken reference, which is the point.

Cite with `@citekey` against `references.bib`. Every factual claim about hardware behaviour needs
either a stamped measurement or a primary source. Textbooks go in "Where to go next" and nowhere
else — see CLAUDE.md §5, which is binding.

## Figures

Three kinds, all declared in `bench/figures.py` and all rendered by `scripts/render-figures.py`:

| Kind | What it is | Where it comes from |
|---|---|---|
| `Table` | A markdown table of measured figures | one stamped result, via a renderer in `bench/tables.py` |
| `Diagram` | An SVG | a function in `bench/diagrams.py` |
| `Listing` | A function's disassembly | one `kind: listing` result per architecture (`make bench-listings`) |

Diagrams are drawn by code, as SVG, deterministically. Not matplotlib: its output embeds font
paths and a version, so `--check` would fail on an upgrade that changed nothing visible, and a
check people learn to ignore is worse than no check.

Every figure must show a mechanism. If it would still make sense with the labels removed, it is
decoration.

### When to draw one

Reach for a diagram whenever the thing being explained has a **shape** — and in a book about
systems that is most of it. Prose is bad at spatial relationships and good at causal ones, so the
division is usually clean:

| Draw it | Write it |
|---|---|
| Where something sits: an address space, a stack frame, a struct's bytes, a cache line | Why it sits there |
| What order things happen in: a toolchain, a trap path, a pipeline stage | What each step decides |
| What is adjacent to what: page-table levels, file-system layers, cores and caches | What it costs |
| Two arrangements of the same thing, side by side | Which one you should prefer, and when |

`bench/diagrams.py` has the vocabulary for those: `cells` for a contiguous row (bits, bytes,
members, blocks), `column` for stacked regions with addresses beside them, `chain` for stages with
arrows between them, plus `heading` and `footnote` so every figure opens and closes the same way.
A chapter's figure function should read as a description of the figure, not as a list of
rectangle coordinates.

The footnote is not optional garnish. A diagram makes a claim, and the line under it is where the
claim is bounded — *this is one core's view*, *addresses are illustrative, run the dumper for
yours*. A figure with no stated limits is the visual form of a number with no conditions.

## Definition of done

PLAN.md §12.3. `[DRAFT]` comes out of the title when every box is ticked, and not before.

**Not when it reaches a length.** There is no page target: a chapter is as long as what it has to
convey. Judge a section at a time — does this one earn its place? — rather than judging the
chapter against a number it was never given.

## Style

British English, direct, active voice, short sentences. No "in this chapter we will". Mathematics
only where it predicts something the reader then checks. Prefer a measurement that surprises the
reader to a rule that reassures them.
