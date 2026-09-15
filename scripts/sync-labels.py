#!/usr/bin/env python3
"""Derive every displayed chapter number from bench/outline.py.

    python3 scripts/sync-labels.py            # rewrite
    python3 scripts/sync-labels.py --check    # fail if anything is out of date (CI)

A chapter's *identity* is its slug, and nothing that has to survive an edit to the outline
contains its number: not the anchor, the filename, the test directory, the checkpoint tag or the
ids of its figures. What is left is the number a reader sees — in the heading, in the sidebar
title, and as the text of a cross-reference — and that is derived here.

This is the rule the book already applies to every other number. A measurement is never typed
into prose because it goes stale silently; a chapter number goes stale in exactly the same way,
and it did, three times, each time leaving behind links whose text disagreed with the chapter
they pointed at. `--strict` cannot see that: the anchor still resolves, only the word next to it
is wrong.

What this does **not** touch is prose that mentions a chapter without linking to it. There is no
way to tell "chapter 15" meaning this book's from "chapter 15" of somebody else's, so those are
left alone and `tests/test_book.py` keeps a lid on them instead.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.outline import CHAPTERS  # noqa: E402

BY_ANCHOR = {chapter.anchor: chapter for chapter in CHAPTERS}

#: Every page whose text may name a chapter. The planning and provenance documents are in here
#: too: they are not published, but they are read constantly while writing, and a plan that names
#: the wrong chapter is worse than one that names none.
PAGES = (
    [ROOT / "index.md", ROOT / "PLAN.md", ROOT / "ORIGINALITY.md", ROOT / "CHECKPOINTS.md"]
    + sorted((ROOT / "chapters").glob("*.md"))
    + sorted((ROOT / "appendices").glob("*.md"))
)

#: `[ch17](#locks-and-memory-ordering)` — the label is display, the anchor is identity.
LINK = re.compile(r"\[ch\d\d\]\(#([a-z0-9-]+)\)")


def sync_links(text: str) -> str:
    def fix(match: re.Match[str]) -> str:
        chapter = BY_ANCHOR.get(match.group(1))
        if chapter is None:  # a part page, an appendix, a section anchor: not ours
            return match.group(0)
        return f"[{chapter.label}](#{chapter.anchor})"

    return LINK.sub(fix, text)


def sync_titles(text: str) -> str:
    """Fix a label sitting immediately before its chapter's title.

    ``## ch01 · Reading C``, ``| ch23 The Memory Hierarchy |``, ``ch08-descriptors`` in a
    checkpoint list — wherever the title is right there, the title is the identity and the number
    beside it is derived. A bare ``ch14`` with nothing to disambiguate it is left alone: there is
    no way to tell this book's from another book's, and guessing is worse than leaving it.
    """
    for chapter in CHAPTERS:
        text = re.sub(
            rf"(?<![#\w])ch\d\d(\s*·\s*|\s+){re.escape(chapter.title)}",
            lambda m, c=chapter: f"{c.label}{m.group(1)}{c.title}",
            text,
        )
    return text


def sync_page(path: Path, text: str) -> str:
    text = sync_titles(sync_links(text))
    for chapter in CHAPTERS:
        if path.name != Path(chapter.path).name:
            continue
        # A stub marks itself [DRAFT] in its frontmatter title; the heading must agree.
        draft = " [DRAFT]" if re.search(r'^title: ".*\[DRAFT\]"$', text, re.M) else ""
        text = re.sub(
            r'^short_title: ".*"$',
            f'short_title: "{chapter.display} · {chapter.title}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^# .*$",
            f"# {chapter.display} · {chapter.title}{draft}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report, do not rewrite")
    args = parser.parse_args()

    stale: list[str] = []
    for path in PAGES:
        original = path.read_text()
        updated = sync_page(path, original)
        if updated == original:
            continue
        stale.append(str(path.relative_to(ROOT)))
        if not args.check:
            path.write_text(updated)

    if args.check and stale:
        print("sync-labels: out of date — run `python3 scripts/sync-labels.py`:")
        for name in stale:
            print(f"  {name}")
        return 1
    verb = "would rewrite" if args.check else "rewrote"
    print(f"sync-labels: OK ({len(stale)} page(s) {verb}, {len(CHAPTERS)} chapters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
