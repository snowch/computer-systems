#!/usr/bin/env python3
"""Create a chapter or appendix stub with the book's standard shape.

    python3 scripts/new-chapter.py 7          # chapters/ch07_virtual_memory.md
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

from bench.outline import APPENDICES, CHAPTERS, Appendix, Chapter  # noqa: E402

#: How a chapter's header names its target. Deliberately not a product name for `host`: ch00
#: states the hardware requirement as a capability, and a header naming one board would be wrong
#: for every reader who bought a different one — which was the state of all nine host chapters
#: until this was fixed.
TARGET_LABEL = {
    "xv6": "`xv6` — the teaching kernel under QEMU",
    "host": "`host` — a RISC-V board, natively ([hardware](#ch00))",
    "both": "`xv6` and `host` — every example says which",
}


#: Present in every generated stub, and absent from a chapter someone has written. Used to
#: decide whether --force is safe: regenerating the template over real prose would destroy work,
#: and "are you sure?" is not a guarantee.
STUB_MARKER = "[To write:"


def chapter_stub(chapter: Chapter, previous: Chapter | None) -> str:
    prerequisites = f"[{previous.label}](#{previous.label})" if previous else "none"
    assumes = f"\n| **Assumes** | {chapter.assumes} |" if chapter.assumes else ""
    return f"""---
title: "{chapter.title} [DRAFT]"
short_title: "{chapter.label} {chapter.title}"
---

({chapter.label})=
# {chapter.label} · {chapter.title} [DRAFT]

:::{{note}} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | {TARGET_LABEL[chapter.target]} |
| **Prerequisites** | {prerequisites} |
| **What it measures** | [To write: the figure this chapter produces, and the result file under `bench/results/` it lands in.] |{assumes}
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

[To write: each problem is a stub under `tests/{chapter.label}/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
"""


def appendix_stub(appendix: Appendix) -> str:
    return f"""---
title: "Appendix {appendix.letter} — {appendix.title} [DRAFT]"
short_title: "Appendix {appendix.letter}"
---

({appendix.label})=
# Appendix {appendix.letter} · {appendix.title} [DRAFT]

[To write: an appendix is a reference, not a chapter. No argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result.]
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
