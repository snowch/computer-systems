#!/usr/bin/env python3
"""Create a chapter or appendix stub with the book's standard shape.

    python3 scripts/new-chapter.py 7          # chapters/virtual_memory.md
    python3 scripts/new-chapter.py --all      # every chapter and appendix that is missing

The seven-part shape comes from PLAN.md §12.1 and is not negotiable: the repetition is what makes
twenty-two chapters read as one book rather than as twenty-two essays. Section five —
*What this cannot tell you* — is the one that is easiest to skip and most important to keep. A
measurement without its limits is a claim.

Refuses to overwrite. A stub is a starting point, not a reset button.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import (  # noqa: E402
    APPENDICES,
    CHAPTERS,
    PART_PAGES,
    Appendix,
    Chapter,
    Part,
    in_part,
)


def by_anchor(anchor: str) -> Chapter:
    return next(c for c in CHAPTERS if c.anchor == anchor)


#: How a chapter's header names its target. Deliberately neither a product name nor an
#: architecture for `host`: appendix H states the requirement as a capability, and a header naming one
#: board would be wrong for every reader who bought a different one — which was the state of all
#: nine host chapters until it was caught.
TARGET_LABEL = {
    "xv6": "`xv6` — the teaching kernel under QEMU",
    "bare": "`bare` — the same machine under QEMU with no operating system on it",
    "host": "`host` — Linux on real hardware, natively ([hardware](#prerequisites-and-setup))",
    "both": "`xv6` and `host` — every example says which",
}


#: Present in every generated stub, and absent from a chapter someone has written. Used to
#: decide whether --force is safe: regenerating the template over real prose would destroy work,
#: and "are you sure?" is not a guarantee.
STUB_MARKER = "[To write:"


def chapter_stub(chapter: Chapter, previous: Chapter | None) -> str:
    prerequisites = f"[{previous.label}](#{previous.anchor})" if previous else "none"
    # The preface tells the reader every stub names the measurements it owes them. A placeholder
    # here made that two-thirds true across twenty-one pages.
    owes = chapter.owes or "[To write: the measurements this chapter must produce.]"
    assumes = f"\n| **Assumes** | {chapter.assumes} |" if chapter.assumes else ""
    answers = (
        "\n| **Answers the cost of** | "
        + ", ".join(f"[{by_anchor(a).label}](#{a})" for a in chapter.answers)
        + " |"
        if chapter.answers
        else ""
    )
    return f"""---
title: "{chapter.title} [DRAFT]"
short_title: "{chapter.label} {chapter.title}"
---

({chapter.anchor})=
# {chapter.label} · {chapter.title} [DRAFT]

:::{{note}} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | {TARGET_LABEL[chapter.target]} |
| **Prerequisites** | {prerequisites} |
| **What it measures** | {owes} |{answers}{assumes}
:::

## The question

{chapter.question}

[To write: one paragraph. State the question this chapter answers and why the previous chapter
leaves it open. No summary of what is to come — the reader can see the headings.]

## The material

[To write: the body. Short sections. Code is quoted from the working tree with
`{{literalinclude}}` and text anchors, never pasted. See AUTHORING_GUIDE.md.]

## What we measured

[To write: `{{include}}` the generated fragments declared in `bench/figures.py`. No number is ever
typed here. For a `host` figure that still needs the board, declare it `pending=` and write the
prose so it reads correctly once the numbers land.]

## What this cannot tell you

[To write. **Mandatory.** What the target, the tooling or the hardware could not show, and what
you did instead. This chapter is not finished while this section is missing.]

## Problems

[To write: each problem is a stub under `{chapter.tests_dir}/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
"""


def appendix_stub(appendix: Appendix) -> str:
    """A stub that says what this appendix will hold and where the content comes from.

    All six used to be the same sentence. That is defensible for a template and indefensible as
    six published pages: a reader who opens Appendix F wanting to know what AArch64 help is coming
    should learn that, and a reader who opens Appendix C should learn that it cannot exist until
    somebody runs the board.
    """
    return f"""---
title: "Appendix {appendix.letter} — {appendix.title} [DRAFT]"
short_title: "Appendix {appendix.letter}"
---

({appendix.label})=
# Appendix {appendix.letter} · {appendix.title} [DRAFT]

:::{{note}} Not written yet
**What it will hold.** {appendix.holds}

**Where it comes from.** {appendix.source}
:::

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

[To write: the reference itself. PLAN.md §4 has the scope.]
"""


def part_stub(part: Part, previous: Part | None) -> str:
    """A stub for a part introduction, in the five sections every one of them has.

    Parts had no page at all for a long time — ``myst.yml`` gave each a title and a list of
    children, which the theme renders as an unclickable heading — and what that could not hold was
    anything part-shaped. Part I's routing note lived inside its own first chapter, so a reader
    who took the advice to skip that chapter only ever saw the note by accident.

    The sections are fixed, and ``tests/test_book.py`` checks all five are present and in order.
    What they must not become is a walk through the part's chapters: that is the sidebar's job and
    the preface's, and a test checks for it.
    """
    chapters = in_part(part)
    first, last = chapters[0], chapters[-1]
    assumes = (
        f"[{previous.name}](#{previous.label})"
        if previous
        else "[ch00](#prerequisites-and-setup), and fluency in some other language"
    )
    return f"""---
title: "{part.title}"
short_title: "Introduction"
---

({part.label})=
# {part.name} · {part.subtitle}

:::{{note}} Part header
:class: dropdown

| | |
|---|---|
| **Chapters** | [{first.label}](#{first.anchor})–[{last.label}](#{last.anchor}) |
| **Target** | {TARGET_LABEL[part.target]} |
| **Assumes** | {assumes} |
:::

## What this part is for

{part.claim}

[To write: what this part asserts, and why it sits here rather than earlier or later. The order of
the parts is an argument; this is where it gets made. No walk through the chapters — the sidebar
already lists them.]

## What it leaves out

[To write: the boundary, and the reason for it. The section a chapter cannot carry, and the one a
reader gets most from: knowing what is out lets them stop worrying about it.]

## Where to start

[To write: routing, not a prerequisite checklist. Who should skip what, and where a reader who is
missing something should go instead.]

## Which machine, and what it cannot tell you

[To write: the target this part runs on, what that buys, and what it forbids. For every part but
Part V that includes stating plainly that nothing here is timed, and why a number from this target
would be worse than no number.]

## Where this leaves you

[To write: a capability, not a summary. What the reader can do at the end that they could not do
at the start.]
"""


class WrittenChapterError(RuntimeError):
    """Refusing to overwrite a chapter that is no longer a stub."""


def write(path: Path, body: str, force: bool) -> bool:
    """Write a stub, refusing to destroy prose.

    ``--force`` exists so the whole set can be regenerated when the template changes — which is
    a normal thing to need, and was needed the day every host chapter's header turned out to name
    a specific board. What it must never do is overwrite a chapter someone has written. The stub
    marker is the test: a real chapter has had every ``[To write: …]`` replaced by then.
    """
    if path.exists():
        if not force:
            return False
        if STUB_MARKER not in path.read_text():
            raise WrittenChapterError(
                f"{path.relative_to(ROOT)} is a written chapter, not a stub — refusing to "
                "overwrite it. Edit it by hand, or delete it first if you really mean to."
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("number", nargs="?", type=int, help="chapter number")
    parser.add_argument("--all", action="store_true", help="every missing chapter and appendix")
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args()

    if not args.all and args.number is None:
        parser.error("give a chapter number, or --all")

    wanted = CHAPTERS if args.all else tuple(c for c in CHAPTERS if c.number == args.number)
    if not wanted:
        parser.error(f"no chapter {args.number} in bench/outline.py")

    written = skipped = 0
    protected: list[str] = []
    for chapter in wanted:
        previous = next((c for c in CHAPTERS if c.number == chapter.number - 1), None)
        try:
            if write(ROOT / chapter.path, chapter_stub(chapter, previous), args.force):
                print(f"  wrote {chapter.path}")
                written += 1
            else:
                skipped += 1
        except WrittenChapterError:
            # Reported at the end rather than raised. Aborting a --force part-way through leaves
            # half the chapters on the new template and half on the old, which is worse than
            # either.
            protected.append(chapter.path)

    if args.all:
        for index, part in enumerate(PART_PAGES):
            previous = PART_PAGES[index - 1] if index else None
            try:
                if write(ROOT / part.path, part_stub(part, previous), args.force):
                    print(f"  wrote {part.path}")
                    written += 1
                else:
                    skipped += 1
            except WrittenChapterError:
                protected.append(part.path)

        for appendix in APPENDICES:
            try:
                if write(ROOT / appendix.path, appendix_stub(appendix), args.force):
                    print(f"  wrote {appendix.path}")
                    written += 1
                else:
                    skipped += 1
            except WrittenChapterError:
                protected.append(appendix.path)

    print(f"\nnew-chapter: {written} file(s) written, {skipped} already present")
    for path in protected:
        print(f"  left alone (written, not a stub): {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
