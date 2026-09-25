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
    [
        ROOT / "index.md",
        ROOT / "PLAN.md",
        ROOT / "ORIGINALITY.md",
        ROOT / "CHECKPOINTS.md",
        # Not published, and that is exactly why they were wrong. `hardware/README.md` is
        # excluded from the book and read straight from the repository, so nothing checked it:
        # its table of hardware-sensitive chapters was stale by two the whole way down, and four
        # of its requirement rows named a chapter that does something else entirely. The others
        # are read constantly while writing, and an authoring guide whose worked example pairs
        # the wrong number with an anchor teaches the mistake it exists to prevent.
        ROOT / "README.md",
        ROOT / "hardware" / "README.md",
        ROOT / "AUTHORING_GUIDE.md",
        ROOT / "ERRATA.md",
    ]
    + sorted((ROOT / "chapters").glob("*.md"))
    + sorted((ROOT / "appendices").glob("*.md"))
)

#: Source files whose *prose* names a chapter. Only :func:`sync_links` is applied to these: the
#: rest of the passes are about a chapter page's own headings and problems, and would be nonsense
#: against Python. ``bench/outline.py`` is here because its ``holds`` and ``source`` fields render
#: onto the appendix pages, so a stale label in a docstring reaches a reader exactly as one in
#: markdown does — three of them had, off by one and by two.
LINK_ONLY = (ROOT / "bench" / "outline.py",)

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

    ``## ch01 · Memory Is One Array``, ``| ch23 The Memory Hierarchy |``, ``ch08-descriptors`` in a
    checkpoint list — wherever the title is right there, the title is the identity and the number
    beside it is derived. A bare ``ch14`` with nothing to disambiguate it is left alone: there is
    no way to tell this book's from another book's, and guessing is worse than leaving it.

    A dash counts as a separator as well as a middle dot, because ``hardware/README.md`` writes the
    pairing as ``ch23 — The Memory Hierarchy`` and that spelling was invisible to this pass for as
    long as the file went unscanned. Every row of that table was two chapters out.
    """
    for chapter in CHAPTERS:
        text = re.sub(
            rf"(?<![#\w])ch\d\d(\s*[·—–]\s*|\s+){re.escape(chapter.title)}",
            lambda m, c=chapter: f"{c.label}{m.group(1)}{c.title}",
            text,
        )
    return text


#: `**4.2 — ` at the start of a problem. The number before the dot is the chapter's, which moves.
PROBLEM = re.compile(r"^\*\*\d+\.(\d+) — ", re.MULTILINE)


def sync_problems(path: Path, text: str) -> str:
    """Renumber a chapter's problems to match the chapter.

    These went stale the same way everything else did: a chapter written as ch04 kept calling its
    problems 4.1 and 4.2 after becoming ch12. The part after the dot is the problem's own and is
    left alone; only the chapter's half is derived.
    """
    chapter = next((c for c in CHAPTERS if path.name == Path(c.path).name), None)
    if chapter is None:
        return text
    return PROBLEM.sub(lambda m: f"**{chapter.number}.{m.group(1)} — ", text)


#: `problem 11.2`, `[ch18](#locks-and-memory-ordering)'s problem 10.2`, and `problems 26.1 and
#: 26.2` — prose *pointing at* a problem, as opposed to the heading that defines one.
#:
#: Every run of whitespace in here is captured rather than matched literally, and put back
#: unchanged. The book is hard-wrapped, so a reference is as likely to straddle a line break as
#: not, and the first version of this pattern spelled those gaps as a single space — which meant
#: `Problem\n21.3` was not a reference as far as the syncer was concerned. It renumbered every
#: reference that happened to fit on one line and silently skipped the ones that did not.
PROBLEM_REFERENCE = re.compile(
    r"(?:\[ch(?P<owner>\d+)\]\(#[\w-]+\)(?P<possessive>['\u2019]s)(?P<pgap>\s+))?"
    r"(?P<word>[Pp]roblems?)(?P<gap>\s+)(?P<chapter>\d+)\.(?P<index>\d+)"
    r"(?:(?P<join>\s+and\s+)(?P<chapter2>\d+)\.(?P<index2>\d+))?"
)


def sync_problem_references(path: Path, text: str) -> str:
    """Renumber prose that points at a problem, the way :func:`sync_problems` renumbers the
    heading that defines one.

    Only the headings were derived, so for a long time every chapter's problems were numbered
    correctly and every sentence pointing at one was not. Thirty-six references across seventeen
    chapters were stale by exactly eight — the width of the two parts inserted ahead of them —
    and being stale by a whole number of chapters is the worst version of this: ch19 said "problem
    11.2", ch11 exists, and ch11 has a second problem. The reader is not sent nowhere. They are
    sent somewhere real and wrong, and nothing in the build can tell.

    A reference names its own chapter's problem unless it is written as another chapter's
    possessive, which is the only form the book uses to point across a chapter boundary. The part
    after the dot is the problem's own and is never touched.
    """
    here = next((c for c in CHAPTERS if path.name == Path(c.path).name), None)

    def renumber(m: re.Match[str]) -> str:
        owner, word, gap = m.group("owner"), m.group("word"), m.group("gap")
        if owner is None:
            # An appendix has no problems of its own, so a reference with no owner named in it is
            # a chapter's own and there is nothing here to derive it from. Appendix G carried
            # `problem 2.2` beside a link to ch04 for three renumberings for exactly that reason;
            # written as ch04's possessive it is maintained like every other.
            if here is None:
                return m.group(0)
            target, prefix = here, ""
        else:
            target = next((c for c in CHAPTERS if c.number == int(owner)), None)
            if target is None:
                return m.group(0)
            prefix = f"[{target.label}](#{target.anchor}){m.group('possessive')}{m.group('pgap')}"
        rewritten = f"{prefix}{word}{gap}{target.number}.{m.group('index')}"
        if m.group("join") is not None:
            rewritten += f"{m.group('join')}{target.number}.{m.group('index2')}"
        return rewritten

    return PROBLEM_REFERENCE.sub(renumber, text)


#: ``| ch03 | `c-for-people-who-will-read-a-kernel` | ...`` — a checkpoint row. The tag is the
#: chapter's identity and the label is its position, so the row can correct itself.
CHECKPOINT_ROW = re.compile(r"^\| ch(\d\d) \| `([a-z0-9-]+)` \|", re.MULTILINE)


def sync_checkpoints(path: Path, text: str) -> str:
    """Renumber CHECKPOINTS.md from the tag in each row.

    The rows are a table rather than links, so :func:`sync_links` never saw them, and inserting a
    chapter left every row below it naming a tag that belongs to a different chapter. The tag is
    derived from the slug and never moves, so it is the half of the row to trust.
    """
    if path.name != "CHECKPOINTS.md":
        return text
    by_tag = {chapter.tag: chapter for chapter in CHAPTERS if chapter.tag}

    def renumber(m: re.Match[str]) -> str:
        chapter = by_tag.get(m.group(2))
        return m.group(0) if chapter is None else f"| {chapter.label} | `{m.group(2)}` |"

    return CHECKPOINT_ROW.sub(renumber, text)


def sync_page(path: Path, text: str) -> str:
    text = sync_checkpoints(
        path, sync_problem_references(path, sync_problems(path, sync_titles(sync_links(text))))
    )
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
    for path in [*PAGES, *LINK_ONLY]:
        original = path.read_text()
        updated = sync_links(original) if path in LINK_ONLY else sync_page(path, original)
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
