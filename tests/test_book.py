"""The book's own structure: outline, table of contents and files on disk agree.

These are cheap and they catch the mistakes that cost the most time — a chapter renamed in one
place and not the other, a chapter whose header claims a target the plan does not give it, a
`{literalinclude}` anchored on a line number that will rot on the first edit above it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

from bench.figures import FIGURES
from bench.outline import (
    APPENDICES,
    CHAPTERS,
    PART_PAGES,
    PARTS,
    TARGET_MACHINE,
    Appendix,
    Chapter,
    Part,
    in_part,
    reading_disassembly,
)
from bench.stamp import ROOT

MYST = yaml.safe_load((ROOT / "myst.yml").read_text())
TOC = MYST["project"]["toc"]
TOC_FILES = [child["file"] for entry in TOC if "children" in entry for child in entry["children"]]

CHAPTER_IDS = [chapter.label for chapter in CHAPTERS]

#: The page that helps a reader choose hardware. It was ch00's "What to buy" until that section
#: became an appendix — it had no stamped result of its own, which makes a thin chapter and a
#: perfectly ordinary reference.
CHOOSING_THE_MACHINE = next(a for a in APPENDICES if a.slug == "choosing_the_machine")

ROMAN_TO_NUMBER = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}

#: Every page a reader reads, in reading order. Generated files are excluded: their prose comes
#: from `bench/figures.py`, so a rule about how to write a sentence cannot be applied to them.
PROSE_FILES = (
    [Path("index.md")]
    + [Path(part.path) for part in PART_PAGES]
    + [Path(chapter.path) for chapter in CHAPTERS]
    + [Path(appendix.path) for appendix in APPENDICES]
)


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_file_exists(chapter: Chapter):
    assert (ROOT / chapter.path).exists(), (
        f"{chapter.path} is in the outline but not on disk — "
        f"run `python3 scripts/new-chapter.py {chapter.number}`"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_is_in_the_table_of_contents(chapter: Chapter):
    assert chapter.path in TOC_FILES, f"{chapter.path} is missing from myst.yml"


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_declares_the_target_the_plan_gives_it(chapter: Chapter):
    """A chapter's header is a promise about which machine its figures came from."""
    header = (ROOT / chapter.path).read_text()
    match = re.search(r"\|\s*\*\*Target\*\*\s*\|([^|]+)\|", header)
    assert match, f"{chapter.path} has no Target row in its header block"
    declared = match.group(1)
    expected = {
        "xv6": "`xv6`",
        "host": "`host`",
        "bare": "`bare`",
        "both": "`xv6` and `host`",
    }[chapter.target]
    assert expected in declared, (
        f"{chapter.path} declares {declared.strip()!r}, but the outline says {chapter.target!r}"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_has_a_label_matching_its_number(chapter: Chapter):
    text = (ROOT / chapter.path).read_text()
    assert f"({chapter.anchor})=" in text, (
        f"{chapter.path} needs a `({chapter.anchor})=` label — the anchor is the slug, "
        f"never the number (bench/outline.py Chapter.anchor)"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_is_described_in_the_plan(chapter: Chapter):
    plan = (ROOT / "PLAN.md").read_text()
    assert chapter.label in plan, f"PLAN.md never mentions {chapter.label}"
    assert chapter.title in plan, f"PLAN.md never names {chapter.title!r}"


def test_every_toc_entry_is_a_real_file():
    for entry in TOC_FILES:
        assert (ROOT / entry).exists(), f"myst.yml lists {entry}, which does not exist"


def test_toc_parts_match_the_outline():
    titles = [entry["title"] for entry in TOC if "title" in entry]
    assert titles[: len(PARTS)] == [part.title for part in PARTS]


PART_IDS = [part.label for part in PART_PAGES]

#: Every part page carries these, in this order. The repetition is the point: a reader who has
#: read one knows where to look on the next, and a part page that is missing one of them has
#: almost certainly drifted into being a summary of its chapters, which is the failure mode the
#: whole idea has to be defended against.
PART_SECTIONS = (
    "## What this part is for",
    "## What it leaves out",
    "## Where to start",
    "## Which machine, and what it cannot tell you",
    "## Where this leaves you",
)


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_part_page_exists(part: Part):
    assert (ROOT / part.path).exists(), f"{part.path} is in the outline but not on disk"


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_part_page_has_a_label_matching_its_number(part: Part):
    text = (ROOT / part.path).read_text()
    assert f"({part.label})=" in text, f"{part.path} needs a `({part.label})=` label"


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_part_page_leads_its_part_in_the_table_of_contents(part: Part):
    """A part introduction that is not the first thing in the part introduces nothing."""
    entry = next((e for e in TOC if e.get("title") == part.title), None)
    assert entry is not None, f"myst.yml has no part titled {part.title!r}"
    children = [child["file"] for child in entry["children"]]
    assert children[0] == part.path, (
        f"{part.title!r} starts with {children[0]}, not its own part page {part.path}"
    )
    assert children[1:] == [chapter.path for chapter in in_part(part)], (
        f"{part.title!r}'s chapters in myst.yml do not match the outline"
    )


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_part_page_has_the_standard_sections(part: Part):
    text = (ROOT / part.path).read_text()
    found = [section for section in PART_SECTIONS if section in text]
    assert found == list(PART_SECTIONS), (
        f"{part.path} is missing or reorders: {[s for s in PART_SECTIONS if s not in found]}"
    )


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_part_page_does_not_summarise_its_chapters(part: Part):
    """The rule the whole idea depends on (CLAUDE.md §7, and the `Part` docstring).

    A part page states a claim and a boundary. The chapter list is already in the sidebar and in
    the preface, and a page that walks its chapters in order is the "in this part we will" filler
    that made bundling the introduction into ch01 look reasonable in the first place.

    Naming chapters is fine and necessary — routing a reader to one is the job. Naming *most of
    them, in order* is the thing being caught.
    """
    text = (ROOT / part.path).read_text()
    # Only the body. The header block's "Chapters" row links the first and last by design, and
    # in a three-chapter part that is already two thirds of a "summary".
    body = text[text.index("## What this part is for") :]
    labels = [chapter.label for chapter in in_part(part)]
    mentioned = [label for label in labels if f"(#{label})" in body]
    assert len(mentioned) < len(labels), (
        f"{part.path} links every one of its chapters ({', '.join(labels)}) — that is a "
        f"table of contents, which the sidebar already is"
    )


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_part_page_states_the_target_rule_it_inherits(part: Part):
    """Three of the five parts may never carry a timing, and each says so on its own page."""
    if part.target in ("host",):
        return
    text = (ROOT / part.path).read_text().lower()
    assert "timed" in text, (
        f"{part.path} is a {part.target!r} part and does not say that nothing in it is timed"
    )


def test_every_part_has_a_page():
    """*Getting started* had no page while it held one chapter, and now it holds two.

    The old rule was that a page whose whole content would be "ch00 is next" is the filler every
    other rule here exists to prevent, and that was right for one chapter. Two chapters is a
    routing decision — the emulated targets are needed immediately and the board is not needed
    until Part V — and routing is exactly what a part page is for.

    So the check inverts rather than disappearing: every part has a page, and a page-less part
    reappearing means someone has split or merged a part without deciding what it is.
    """
    pageless = [part.name for part in PARTS if not part.page]
    assert not pageless, (
        f"a part with no page has appeared: {', '.join(pageless)} — decide whether it is really "
        "a part, and give it a page if it is"
    )


NUMBERED = re.compile(r"(?<![A-Za-z0-9])ch\d\d(?![0-9])")


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_no_identifier_carries_the_chapter_number(chapter: Chapter):
    """The rule the whole scheme rests on (``Chapter.anchor``).

    A chapter's number says where it currently sits. This book has moved that three times, and
    each move renamed every identifier downstream of it: anchors, filenames, test directories,
    checkpoint tags, figure ids, and every permalink anyone had bookmarked. So none of those may
    contain it. What may, and must, is the text a reader sees — and that is derived by
    ``scripts/sync-labels.py`` and checked in CI.
    """
    identifiers = {
        "anchor": chapter.anchor,
        "path": chapter.path,
        "tests_dir": chapter.tests_dir,
        "tag": chapter.tag or "",
        "figure id": chapter.figure("example"),
    }
    offenders = {k: v for k, v in identifiers.items() if NUMBERED.search(v)}
    assert not offenders, (
        f"{chapter.label}'s {', '.join(offenders)} still carries its number: {offenders} — "
        f"identifiers are slugs, so that inserting a chapter renames nothing"
    )


def test_every_figure_id_belongs_to_a_chapter_or_appendix_by_name():
    """A figure id is an identifier too, and drifted the same way before this existed."""
    from bench.figures import FIGURES

    known = tuple(c.anchor for c in CHAPTERS) + tuple(a.label for a in APPENDICES)
    stragglers = [
        name
        for name in FIGURES
        if NUMBERED.search(name) or not any(name.startswith(prefix) for prefix in known)
    ]
    assert not stragglers, f"figure ids not named after a chapter or appendix: {stragglers}"


def test_displayed_chapter_numbers_match_the_outline():
    """What ``scripts/sync-labels.py --check`` enforces, as a test as well.

    ``myst build --strict`` cannot catch this: a link reading ``[ch17](#virtual-memory)`` resolves
    perfectly and is simply wrong about which chapter it is sending the reader to. That is the
    exact bug the old numeric anchors produced four times in the preface alone.
    """
    import subprocess

    result = subprocess.run(
        [sys.executable, "scripts/sync-labels.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


LITERALINCLUDE_SOURCE = re.compile(r"\{literalinclude\}\s+\.\./(\S+\.c)")


def _programs_quoted_by(text: str) -> set[str]:
    """The runnable programs a chapter shows, by name.

    Library sources and the bare-metal runtime are quoted too and are not programs — a reader
    cannot run `console.c`. The registry is what decides, so a file moving between the two
    categories does not need remembering here as well.
    """
    from bench.programs import PROGRAMS

    by_path = {program.relative: program for program in PROGRAMS}
    return {
        by_path[match].name for match in LITERALINCLUDE_SOURCE.findall(text) if match in by_path
    }


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_a_chapter_that_shows_a_program_says_how_to_run_it(chapter: Chapter):
    """The gap this closes was real and was worst exactly where it mattered most.

    Part II quoted seven bare-metal programs across six chapters and never once said how to build
    one. The flags are not guessable — `-fno-pic`, `-mcmodel=medany`, a linker script, `-bios
    none` — and they were only ever written down in a Python module a reader has no reason to
    open. A book whose whole question is *how would I know?* has to let the reader try it.
    """
    text = (ROOT / chapter.path).read_text()
    quoted = _programs_quoted_by(text)
    missing = sorted(name for name in quoted if f"./run {name}" not in text)
    assert not missing, (
        f"{chapter.path} shows {', '.join(missing)} and never says how to run "
        f"{'them' if len(missing) > 1 else 'it'} — add `./run {missing[0]}`"
    )


#: Spelled-out numbers, which is how this book writes a count in prose. Digits in prose are
#: already policed by `scripts/verify-numbers.py`; words are the hole it cannot see through, and
#: three real contradictions went in through it — a preface claiming four parts and twenty-four
#: chapters, a status box that went stale twice, and a chapter saying "one instruction each"
#: directly above a generated caption saying two.
NUMBER_WORDS = {
    word: value
    for value, word in enumerate(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
            "twenty",
        ]
    )
}
NUMBER_WORDS.update(
    {
        "twenty-one": 21,
        "twenty-two": 22,
        "twenty-three": 23,
        "twenty-four": 24,
        "twenty-five": 25,
        "twenty-six": 26,
        "twenty-seven": 27,
        "twenty-eight": 28,
        "twenty-nine": 29,
        "thirty": 30,
        "thirty-one": 31,
        "thirty-two": 32,
    }
)

#: The preface's claims about the shape of the whole book. Narrow on purpose: "Five chapters
#: depend on the reference machine" is a true statement about a subset and has to stay sayable, so
#: only a claim about a total is checked, and only where the preface makes one.
TOTAL_CLAIMS = (
    (re.compile(r"in (\S+) parts and (\S+) chapters"), ("parts", "chapters")),
    (re.compile(r"All (\S+) chapters are written"), ("chapters",)),
    (re.compile(r"(\S+) of the (\S+) chapters are written"), ("written", "chapters")),
    (re.compile(r"(\S+) of the (\S+) appendices"), ("written_appendices", "appendices")),
    # Added when Part II's `bare` target went unmentioned on the page whose job is to say what
    # the book runs on. The preface said "two" for as long as there had been three.
    (re.compile(r"## (\S+) targets on (\S+) machines"), ("targets", "machines")),
    # The board has not reported, so this one grows every time a Part V figure is declared. It
    # said thirteen while nineteen were waiting.
    (re.compile(r"(\S+) figures are marked \*pending\*"), ("pending",)),
    (
        re.compile(r"picks one target and lives with its limitations\. This one uses\s+(\S+?),"),
        ("targets",),
    ),
    (re.compile(r"is setup: all (\S+) targets working"), ("targets",)),
)


def test_the_prefaces_counts_agree_with_the_outline():
    """A count written as a word is still a number, and still goes stale.

    `scripts/verify-numbers.py` polices digits in prose and cannot see through a word, which is
    how the preface came to claim four parts and twenty-four chapters, and how its status box went
    stale twice more. This checks only the sentences that state a total, because a subset claim is
    legitimate and common.

    It also insists the preface still makes at least one such claim, so that rewording a sentence
    cannot quietly retire the check along with it.
    """
    text = (ROOT / "index.md").read_text()
    written = len([c for c in CHAPTERS if "[DRAFT]" not in (ROOT / c.path).read_text()])
    truth = {
        # The numbered parts. *Getting started* has a page now that it holds two chapters,
        # but it is front matter and there is no Part VI.
        "parts": len([part for part in PART_PAGES if part.number >= 1]),
        "chapters": len(CHAPTERS),
        "written": written,
        "appendices": len(APPENDICES),
        "written_appendices": len(
            [a for a in APPENDICES if "[DRAFT]" not in (ROOT / a.path).read_text()]
        ),
        # "both" is a way of saying two of the others, not a target of its own.
        "pending": len([f for f in FIGURES.values() if getattr(f, "pending", None)]),
        "targets": len(TARGET_MACHINE),
        "machines": len(set(TARGET_MACHINE.values())),
    }

    wrong, matched, seen = [], 0, set()
    for pattern, names in TOTAL_CLAIMS:
        for found in pattern.finditer(text):
            matched += 1
            seen.update(names)
            for word, name in zip(found.groups(), names, strict=True):
                value = NUMBER_WORDS.get(word.lower())
                if value is None:
                    wrong.append(
                        f"{word!r} is not a number this check can read, in {found.group(0)!r}"
                    )
                elif value != truth[name]:
                    wrong.append(f"the preface says {word} {name}; the outline has {truth[name]}")
    assert matched, (
        "the preface no longer states how many chapters, parts or appendices the book has in any "
        "form this check recognises — reword it back, or teach TOTAL_CLAIMS the new shape"
    )
    # `matched` alone is too weak for these two. A claim whose wording drifts stops matching its
    # pattern and is then checked by nothing, silently — which is how "two targets" survived the
    # arrival of a third. Naming them here means rewording the heading fails loudly instead.
    missing = {"targets", "machines"} - seen
    assert not missing, (
        f"the preface no longer states how many {' or '.join(sorted(missing))} the book has in a "
        f"form this check recognises — the count that went stale once already, so reword it back "
        f"or teach TOTAL_CLAIMS the new shape"
    )
    assert not wrong, "\n".join(wrong)


INCLUDES_A_FIGURE = re.compile(r"```\{include\}\s+_generated/([\w-]+)\.md\s*\n```")
#: "One instruction each", "two instructions in total" — prose claiming to count a whole listing.
#: "One instruction in `acquire` does the mutual exclusion" counts a subset and is not this.
COUNTS_THE_WHOLE_LISTING = re.compile(
    r"\b([A-Za-z]+(?:-[a-z]+)?|\d+)\s+instructions?\s+(?:each|in total|altogether)\b",
    re.IGNORECASE,
)
CAPTION_COUNT = re.compile(r"(\d+)\s+instructions?\b")


def test_prose_beside_a_listing_agrees_with_it_about_how_many_instructions():
    """The third contradiction, and the one no existing check could have caught.

    ch01 said "One instruction each" in the paragraph under a listing whose own caption, generated
    from a stamped result, said two. Both numbers were on the same screen. `--strict` sees a valid
    document and `verify-numbers.py` sees no digits in the prose, because the prose spelled it.
    """
    wrong = []
    for chapter in CHAPTERS:
        text = (ROOT / chapter.path).read_text()
        for match in INCLUDES_A_FIGURE.finditer(text):
            generated = ROOT / "chapters" / "_generated" / f"{match.group(1)}.md"
            if not generated.exists():
                continue
            stated = CAPTION_COUNT.search(generated.read_text())
            if not stated:
                continue
            # The paragraph immediately after the include is the one talking about this listing.
            after = text[match.end() : match.end() + 400]
            for word in COUNTS_THE_WHOLE_LISTING.findall(after):
                claimed = int(word) if word.isdigit() else NUMBER_WORDS.get(word.lower())
                if claimed is None or claimed == int(stated.group(1)):
                    continue
                wrong.append(
                    f"{chapter.path} says {word!r} instructions beside {match.group(1)}, "
                    f"whose caption says {stated.group(1)}"
                )
    assert not wrong, "\n".join(wrong)


PREREQUISITE_ROW = re.compile(r"\|\s*\*\*Prerequisites\*\*\s*\|([^|]*)\|")
LINKED_ANCHOR = re.compile(r"\(#([a-z0-9-]+)\)")


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_a_prerequisite_comes_earlier_than_the_chapter_that_needs_it(chapter: Chapter):
    """A chapter cannot require one the reader has not reached.

    ch03, in Part I, declared ch11 — *Representing Information*, eight chapters later in Part III.
    Nothing caught it. The link resolved, so `--strict` was satisfied; the label was derived from
    the anchor, so it was not stale; and `answers` had a backwards check while the row a reader
    actually acts on had none. It survived two renumbers and a rewrite of the whole labelling
    scheme because every check was looking at whether the reference *worked*, not at whether it
    pointed somewhere the reader had been.
    """
    text = (ROOT / chapter.path).read_text()
    row = PREREQUISITE_ROW.search(text)
    assert row, f"{chapter.path} has no Prerequisites row"

    by_anchor = {c.anchor: c for c in CHAPTERS}
    forward = []
    for anchor in LINKED_ANCHOR.findall(row.group(1)):
        needed = by_anchor.get(anchor)  # part pages and appendices are not chapters
        if needed is not None and needed.number >= chapter.number:
            forward.append(f"{needed.label} ({needed.title})")
    assert not forward, (
        f"{chapter.label} lists {', '.join(forward)} as a prerequisite, which the reader has "
        f"not reached yet"
    )


SPELLED_OUT_CHAPTER_LINK = re.compile(r"\[[Cc]hapter \d+\]\(#")


def test_every_chapter_link_uses_the_books_own_form():
    """`[ch21](#anchor)`, never `[Chapter 20](#anchor)`.

    Not a style rule. `scripts/sync-labels.py` derives the number in a link from the anchor it
    points at, and it recognises one spelling; a link written the other way is outside the check
    and drifts silently. Four of the ten that existed had gone off by one when a chapter was
    inserted into Part II, all of them in the preface, all of them still resolving perfectly.
    """
    offenders = []
    for path in [
        ROOT / "index.md",
        *sorted((ROOT / "chapters").glob("*.md")),
        *sorted((ROOT / "appendices").glob("*.md")),
    ]:
        for found in SPELLED_OUT_CHAPTER_LINK.findall(path.read_text()):
            offenders.append(f"{path.name}: {found!r}")
    assert not offenders, "these are outside sync-labels.py's reach and will drift: " + "; ".join(
        offenders
    )


PART_SELF = {part.path: part.number for part in PART_PAGES}

#: Regions a part mention is allowed to be plain text in: frontmatter, code, a heading, a MyST
#: label or directive, a comment, and the inside of a link that is already there.
NOT_PROSE = (
    (re.compile(r"\A---\n.*?\n---\n", re.S), 0),
    (re.compile(r"```.*?```", re.S), 0),
    (re.compile(r"`[^`\n]+`"), 0),
    (re.compile(r"^#{1,6} .*$", re.M), 0),
    (re.compile(r"^\(\w+\)=.*$", re.M), 0),
    (re.compile(r"^:::.*$", re.M), 0),
    (re.compile(r"^%.*$", re.M), 0),
    (re.compile(r"\[[^\]\n]*\]\([^)\n]*\)"), 0),
)


def _prose_mentions_of_a_part(text: str) -> list[tuple[int, str]]:
    """Every ``Part IV`` in running prose, as (line number, roman numeral).

    Plural enumerations — "Parts I, II and III" — are not references to one part and are left
    alone; ``\bPart `` does not match them, which is the whole reason the word is singular here.
    """
    skip = [m.span() for pattern, _ in NOT_PROSE for m in pattern.finditer(text)]
    return [
        (text[: m.start()].count("\n") + 1, m.group(1))
        for m in re.finditer(r"\bPart (I{1,3}|IV|V)\b", text)
        if not any(a <= m.start() < b for a, b in skip)
    ]


@pytest.mark.parametrize("path", PROSE_FILES, ids=[str(p) for p in PROSE_FILES])
def test_every_prose_mention_of_a_part_is_a_link(path):
    """A part reference is a link, every time, exactly as a chapter reference is.

    The book links a chapter on every mention — the same ``chNN`` target appears as a link seven
    times in one paragraph of ch00 — so a part that is a link once at the top of a page and plain
    text for the next two hundred lines reads as an oversight rather than as restraint. It was
    one: the preface said "The kernel Part IV reads has its own commentary" six lines below a
    table that linked Part IV, and the bare one is the one a reader meets in a sentence.

    A page does not link to itself, so a part page's own number is exempt.
    """
    text = (ROOT / path).read_text()
    mine = PART_SELF.get(str(path))
    bare = [
        f"line {line}: Part {roman}"
        for line, roman in _prose_mentions_of_a_part(text)
        if ROMAN_TO_NUMBER[roman] != mine
    ]
    assert not bare, (
        f"{path} names a part in prose without linking it, and every chapter reference on the "
        f"same page is a link:\n  " + "\n  ".join(bare)
    )


#: "Three chapters and one job", "Six chapters, each building one primitive" — a *paragraph*
#: opening by counting chapters.
#:
#: Anchored to a paragraph rather than a line. These files are hard-wrapped, so a line break falls
#: wherever the column runs out: part2 says "the alternative ordering puts three chapters of file
#: format between you and the first interesting thing", and "three chapters" landed at the start
#: of a line. That is a subset claim mid-sentence and has to stay sayable, exactly as the
#: preface's "Five chapters depend on the reference machine" does.
COUNTS_ITS_CHAPTERS = re.compile(r"(?:\A|\n\n)(\S+) chapters\b", re.I)


@pytest.mark.parametrize("part", PART_PAGES, ids=[p.label for p in PART_PAGES])
def test_a_part_that_counts_its_chapters_counts_them_right(part: Part):
    """The preface's totals are checked; a part page's were not, and they are the same claim.

    Part I opens "Three chapters and one job" and Part II "Six chapters, each building one
    primitive". Both are true, both are typed, and neither was derived from anything — so
    inserting a chapter into either part would have left the page contradicting its own header,
    which lists the chapter range two lines above and is generated.

    Only an opening sentence that starts by counting is checked. A part is free to say "three of
    these" about a subset further down, exactly as the preface is.
    """
    text = (ROOT / part.path).read_text()
    actual = len(in_part(part))
    wrong = [
        f"{part.path} says {word} chapters; the outline gives it {actual}"
        for word in COUNTS_ITS_CHAPTERS.findall(text)
        if NUMBER_WORDS.get(word.lower()) not in (None, actual)
    ]
    assert not wrong, "\n".join(wrong)


#: A ``{literalinclude}`` directive with its options, as one block.
LITERALINCLUDE = re.compile(r"```\{literalinclude\}\s+(\S+)\n((?::[^\n]*\n)*)```")


def _c_includes(path: str) -> list[tuple[str, str]]:
    """Every literalinclude of C or a C header on a page, as (file, options)."""
    return [
        (target, options)
        for target, options in LITERALINCLUDE.findall((ROOT / path).read_text())
        if target.endswith((".c", ".h"))
    ]


def test_the_first_whole_program_is_the_first_whole_program():
    """ch01 opens "Every piece of C you have seen in this book so far has been a fragment".

    That is the hook of its first section and the reason the next listing lands: the reader has
    seen functions and never a program, so a `#include` and a `main` are worth naming. Only ch00
    shows C before it, and the claim holds exactly as long as every listing there stays anchored.
    An unanchored include added to ch00 would show a whole file and make ch01 open on something
    untrue, with nothing in the build to notice — the anchors would all still resolve.
    """
    unanchored = [
        target
        for target, options in _c_includes("chapters/prerequisites_and_setup.md")
        if ":start-at:" not in options
    ]
    assert not unanchored, (
        "ch00 now shows a whole C file, so ch01's \"every piece of C so far has been a "
        f'fragment" is no longer true: {", ".join(unanchored)}'
    )

    whole = [
        target
        for target, options in _c_includes("chapters/memory_is_one_array.md")
        if ":start-at:" not in options
    ]
    assert whole, (
        'ch01 says "here is a complete one" and no longer includes a whole C file to back it'
    )


#: PLAN.md §12.1, as a chapter's own headings. "Header block" is the note table rather than a
#: heading, so it is not listed; the other six are.
#: ``| **Chapters** | [ch02](#reading-a-listing)–[ch05](#…) |`` — the header's range.
APPENDIX_LINK = re.compile(r"\[Appendix ([A-Z])\]\(#([\w-]+)\)")


@pytest.mark.parametrize("path", PROSE_FILES, ids=[str(p) for p in PROSE_FILES])
def test_an_appendix_link_points_at_that_appendix(path):
    """`sync-labels` derives a chapter link's text; nothing derived an appendix's.

    ch03 said "[Appendix A](#reading-a-listing)" after the listing key moved out of appendix A and
    became a chapter that took the anchor with it. The link resolved perfectly — to a chapter —
    and `--strict` cannot see the difference between a link that works and one that says where it
    goes. This is the same shape as every other finding in this book's review passes, and the only
    one of them that is a single regular expression.
    """
    text = (ROOT / path).read_text()
    wrong = [
        f"{m.group(0)} should point at #appendix-{m.group(1).lower()}"
        for m in APPENDIX_LINK.finditer(text)
        if m.group(2) != f"appendix-{m.group(1).lower()}"
    ]
    assert not wrong, f"{path} names an appendix and links elsewhere:\n  " + "\n  ".join(wrong)


CHAPTERS_ROW = re.compile(r"\| \*\*Chapters\*\* \| (.+?) \|")


@pytest.mark.parametrize("part", PART_PAGES, ids=PART_IDS)
def test_a_part_header_names_its_own_first_and_last_chapter(part: Part):
    """The range in the header block is the part's, and the part's boundaries move.

    `sync-labels` keeps the *labels* honest, so this row reads plausibly however wrong it is: when
    a chapter was inserted at the front of Part I, the row went on pointing at the chapter that
    used to be first and simply relabelled it. The anchors are the part that cannot be derived
    from the link itself, so they are what this checks.
    """
    text = (ROOT / part.path).read_text()
    row = CHAPTERS_ROW.search(text)
    assert row, f"{part.path} has no Chapters row in its header block"
    anchors = re.findall(r"\(#([\w-]+)\)", row.group(1))
    chapters = in_part(part)
    assert anchors and anchors[0] == chapters[0].anchor, (
        f"{part.path} opens its range at #{anchors[0] if anchors else '?'}, but the part starts "
        f"at {chapters[0].label} (#{chapters[0].anchor})"
    )
    assert anchors[-1] == chapters[-1].anchor, (
        f"{part.path} ends its range at #{anchors[-1]}, but the part ends at "
        f"{chapters[-1].label} (#{chapters[-1].anchor})"
    )


CHAPTER_SECTIONS = (
    "## The question",
    "## The material",
    "## What we measured",
    "## What this cannot tell you",
    "## Problems",
    "## Where to go next",
)


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_has_the_seven_part_shape(chapter: Chapter):
    """§12.1 says seven parts in this order, every time, and nothing checked it.

    The part pages have had this check since they existed. The chapters, which is where the rule
    actually comes from, did not — so ch00 was the only chapter of thirty-two with no "## The
    material" at all, and a chapter split out of it put that heading in and then left its three
    body sections beside the heading rather than under it. Both read fine in isolation and both
    break the shape the other thirty-one keep.
    """
    text = (ROOT / chapter.path).read_text()
    found = [section for section in CHAPTER_SECTIONS if section in text]
    assert found == list(CHAPTER_SECTIONS), (
        f"{chapter.path} is missing or reorders: {[s for s in CHAPTER_SECTIONS if s not in found]}"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_a_chapters_body_sits_under_the_material(chapter: Chapter):
    """Everything between *The material* and *What we measured* is a subsection of it.

    A `##` there is a seventh top-level section, which is the shape §12.1 forbids — and it is an
    easy one to introduce when sections move between chapters, because promoting `###` to `##` is
    what moving them usually needs.
    """
    text = (ROOT / chapter.path).read_text()
    body = text[text.index("## The material") + 1 : text.index("## What we measured")]
    stray = [line for line in body.split("\n") if line.startswith("## ")]
    assert not stray, (
        f"{chapter.path} has a top-level heading inside the body — it belongs under "
        f"*The material*: {stray}"
    )


BIB_ENTRY = re.compile(r"@(\w+)\{([^,]+),(.*?)\n\}", re.S)


def test_every_reference_can_be_followed():
    """A citation the reader cannot follow is half a citation.

    §5 requires every factual claim about hardware to cite a measurement or a primary source, and
    the whole point of naming the source is that the reader can go and read it. The preface's
    "Cox et al. (n.d.)" and "Gregg (2020)" rendered as blue, underlined, and inert: the theme
    styles a citation as a link whether or not it has anywhere to go, which on a phone — where
    there is no hover card — is indistinguishable from a broken link.

    Sixteen of the twenty entries had the address all along, in ``howpublished``, which is the
    BibTeX-correct field for a web resource and the one myst's renderer does not read. It reads
    ``url`` and ``doi``. So this asks for one of those, and ``howpublished`` stays for the sake of
    any other tool that opens this file.
    """
    text = (ROOT / "references.bib").read_text()
    entries = BIB_ENTRY.findall(text)
    assert len(entries) > 15, f"only {len(entries)} entries parsed — has the format changed?"
    unfollowable = [
        key.strip() for _, key, body in entries if not re.search(r"^\s*(url|doi)\s*=", body, re.M)
    ]
    assert not unfollowable, (
        "these references give the reader nowhere to go — add a `url` or a `doi`, because the "
        "citation renders as a link either way:\n  " + "\n  ".join(unfollowable)
    )


def test_appendices_exist_and_are_listed():
    for appendix in APPENDICES:
        assert (ROOT / appendix.path).exists(), appendix.path
        assert appendix.path in TOC_FILES, f"{appendix.path} is missing from myst.yml"


def test_no_literalinclude_is_anchored_on_a_line_number():
    """Line numbers rot the first time anything above them is edited (AUTHORING_GUIDE.md)."""
    offenders = []
    for source in sorted((ROOT / "chapters").glob("*.md")) + sorted(
        (ROOT / "appendices").glob("*.md")
    ):
        text = source.read_text()
        for block in re.finditer(r"```\{literalinclude\}(.*?)```", text, re.DOTALL):
            if re.search(r"^:lines:", block.group(1), re.MULTILINE):
                offenders.append(source.name)
    assert not offenders, f"anchor on :start-at:/:end-before: text instead: {offenders}"


def test_literalinclude_targets_exist():
    missing = []
    for source in sorted((ROOT / "chapters").glob("*.md")):
        for match in re.finditer(r"```\{literalinclude\}\s+(\S+)", source.read_text()):
            target = (source.parent / match.group(1)).resolve()
            if not target.exists():
                missing.append(f"{source.name} -> {match.group(1)}")
    assert not missing, f"literalinclude points at files that do not exist: {missing}"


def test_written_chapters_have_an_originality_entry():
    """CLAUDE.md §5: the entry lands in the same commit as the chapter."""
    originality = (ROOT / "ORIGINALITY.md").read_text()
    for chapter in CHAPTERS:
        text = (ROOT / chapter.path).read_text()
        if "[DRAFT]" in text:
            continue
        # The heading, not the label anywhere in the file. A passing mention in another
        # chapter's entry — or in a footer saying which chapters are still stubs — used to
        # satisfy this, which is how ch28 briefly had no entry and a green test.
        assert f"## {chapter.label} ·" in originality, (
            f"{chapter.label} has lost its [DRAFT] marker but ORIGINALITY.md has no "
            f"'## {chapter.label} ·' section for it"
        )


def test_index_and_docs_are_excluded_from_the_book_build():
    excluded = MYST["project"]["exclude"]
    for document in ("PLAN.md", "CLAUDE.md", "AUTHORING_GUIDE.md", "ORIGINALITY.md"):
        assert document in excluded, f"{document} would be published as a chapter"


def test_repository_licences_are_split():
    """Prose is CC-BY-NC-4.0, code is Apache-2.0, and xv6 keeps its own MIT licence."""
    assert "Attribution-NonCommercial" in (ROOT / "LICENSE").read_text()
    assert "Apache License" in (ROOT / "LICENSE-CODE").read_text()
    assert MYST["project"]["license"] == {"content": "CC-BY-NC-4.0", "code": "Apache-2.0"}
    assert Path(ROOT / "xv6" / "xv6-riscv" / "LICENSE").exists(), (
        "the xv6 submodule must keep its own MIT licence file"
    )


# -- the hardware prompt ------------------------------------------------------------------

PROMPT = ROOT / "hardware" / "find-a-board.txt"


def test_the_board_prompt_keeps_its_non_negotiables():
    """The prompt is what a reader shops against, so it must not quietly lose a requirement.

    The counter requirement is the one that matters: it is the only one with no workaround, it is
    not printed on the box, and on RISC-V it depends on the firmware rather than the chip. A
    prompt that dropped it would send someone to buy a board that cannot run Part V.
    """
    text = PROMPT.read_text()
    for required in (
        "perf stat -e cycles,instructions",
        "<not supported>",
        "perf record",
    ):
        assert required in text, f"the board prompt no longer mentions {required!r}"


def test_the_board_prompt_keeps_the_riscv_warning():
    """Hard-won, and the reason Part V is not on RISC-V. It must not be quietly dropped.

    A reader who asks for a RISC-V board should be told which of counting and sampling actually
    works on the core they are considering, because the answer differs per core and no product
    listing says.
    """
    text = PROMPT.read_text()
    for required in ("U74", "SBI PMU", "CONFIG_RISCV_PMU_SBI", "rv64imafdc", "u_mode_cycle"):
        assert required in text, f"the RISC-V warning no longer mentions {required!r}"


def test_the_board_prompt_asks_for_sources_and_admits_uncertainty():
    """An LLM guessing confidently about perf support is the failure mode this guards against."""
    text = PROMPT.read_text().lower()
    assert "source" in text
    assert "unsure" in text or "uncertain" in text


def test_the_board_prompt_has_placeholders_to_fill_in():
    text = PROMPT.read_text()
    assert "[YOUR COUNTRY]" in text
    assert "[YOUR BUDGET]" in text


def test_the_board_prompt_is_linked_rather_than_copied():
    """One source of truth for the prompt, wherever it is quoted.

    It used to be `{literalinclude}`d into ch00, back when the reference machine was a RISC-V
    board that was genuinely hard to buy and finding one was a chapter's worth of work. Now the
    chapter recommends a Pi 5, every Pi 5 works, and shopping advice is not what a setup chapter
    is for — so the prompt stays in `hardware/`, where a reader who cannot get one will look, and
    ch00 points at it in a sentence.

    What this still guards is the copy: no page may paste the prompt's text, because two copies
    of a list of requirements drift and the stale one is the one somebody shops against.
    """
    prompt = (ROOT / "hardware" / "find-a-board.txt").read_text()
    signature = next(line for line in prompt.splitlines() if "HARD REQUIREMENTS" in line)
    notes = (ROOT / "hardware" / "README.md").read_text()
    assert "find-a-board.txt" in notes, "hardware/README.md no longer points at the prompt"
    assert signature not in notes, "hardware/README.md has pasted the prompt instead of linking it"

    page = (ROOT / CHOOSING_THE_MACHINE.path).read_text()
    assert "hardware/README.md" in page, "appendix H no longer points anywhere for the alternative"
    assert signature not in page, "appendix H has pasted the prompt"


def test_the_hardware_notes_are_not_published_as_a_chapter():
    assert "hardware/README.md" in MYST["project"]["exclude"]


# -- chapters that depend on the reference hardware ---------------------------------------

HARDWARE_SENSITIVE = [chapter for chapter in CHAPTERS if chapter.assumes]


def test_some_chapters_declare_a_hardware_assumption():
    """A guard on the guard: if this list empties, the checks below stop checking anything."""
    assert HARDWARE_SENSITIVE, "bench/outline.py records no hardware assumptions at all"


@pytest.mark.parametrize("chapter", HARDWARE_SENSITIVE, ids=[c.label for c in HARDWARE_SENSITIVE])
def test_hardware_assumption_is_in_the_chapter_header(chapter: Chapter):
    """Readers open one chapter, not the whole book. The warning has to be where they land."""
    header = (ROOT / chapter.path).read_text()
    assert "| **Assumes** |" in header, (
        f"{chapter.path} assumes something about the reference core but its header does not "
        "say so — regenerate the stub, or add the row by hand if the chapter is written"
    )


@pytest.mark.parametrize("chapter", HARDWARE_SENSITIVE, ids=[c.label for c in HARDWARE_SENSITIVE])
def test_the_hardware_appendix_names_every_hardware_sensitive_chapter(chapter: Chapter):
    """The buying advice promises a complete list. A chapter added later must not escape it.

    The list moved out of ch00 with the rest of the shopping, which is why this asks appendix H
    rather than the chapter. What it checks is unchanged: a chapter that declares `assumes` is
    making a claim about the reader's hardware, and the page that helps them choose hardware has
    to say so before they spend the money.
    """
    page = (ROOT / CHOOSING_THE_MACHINE.path).read_text()
    section = page[page.index("## Which chapters actually depend on the hardware") :]
    assert f"[{chapter.label}](#{chapter.anchor})" in section, (
        f"{chapter.label} assumes something about the hardware but appendix H's list omits it"
    )


def test_host_chapter_headers_do_not_name_a_specific_board():
    """The hardware requirement is a capability (ch00), so a header naming one board is wrong.

    Every host chapter said 'VisionFive 2 Lite' until this was caught — nine chapters that would
    have been inaccurate for any reader who bought something else. The reference machine has since
    changed once, which is the argument for this test rather than against it: the pattern names
    both the old board and the current one, because a header pinned to either is the same mistake.

    Two exemptions, both by construction. ch00 is the chapter that recommends a specific machine,
    and does so in its body, having first said what the machine has to be able to do. And the
    **Assumes** row is where naming the reference core is the whole point — a chapter that depends
    on a 4-wide out-of-order pipeline has to say which one it measured, or the row tells the reader
    nothing they can act on.
    """
    offenders = []
    for chapter in CHAPTERS:
        if chapter.target != "host":
            continue
        header = (ROOT / chapter.path).read_text().split(":::", 2)[1]
        rows = [row for row in header.splitlines() if not row.startswith("| **Assumes** |")]
        if re.search(r"VisionFive|StarFive|JH7110|Raspberry|BCM2712|Cortex-A", "\n".join(rows)):
            offenders.append(chapter.label)
    assert not offenders, f"these host chapters name a specific board in their header: {offenders}"


def test_every_stub_carries_the_marker_that_protects_written_chapters():
    """--force decides what is safe to overwrite by looking for this marker.

    A stub generated without it would be indistinguishable from a written chapter, and would
    quietly stop being regenerated when the template changes.
    """
    for chapter in CHAPTERS:
        text = (ROOT / chapter.path).read_text()
        if "[DRAFT]" not in text:
            continue
        assert "[To write:" in text, f"{chapter.path} is a draft but carries no stub marker"


def test_the_hardware_advice_carries_its_caveat():
    """The book points readers at third-party tools and then at shops. Both pages say whose
    decision that is, and the note is the kind of thing that gets tidied away in an edit."""
    notes = (ROOT / "hardware" / "README.md").read_text()
    chapter = (ROOT / CHOOSING_THE_MACHINE.path).read_text()
    for text, where in ((notes, "hardware/README.md"), (chapter, "ch00")):
        lowered = text.lower()
        assert "return policy" in lowered, f"{where} does not mention checking the return policy"
        assert "warranty" in lowered, f"{where} does not disclaim a warranty"
    assert "The purchase is yours and so is the risk" in notes


# -- the spine across the seam ------------------------------------------------------------

PAIRED = [chapter for chapter in CHAPTERS if chapter.answers]


def test_some_chapters_name_the_chapter_whose_cost_they_measure():
    """A guard on the guard. If this empties, the two halves have stopped being one book."""
    assert PAIRED, "no chapter in bench/outline.py names an earlier chapter it costs"


@pytest.mark.parametrize("chapter", PAIRED, ids=[c.label for c in PAIRED])
def test_pairings_point_backwards_at_real_chapters(chapter: Chapter):
    """A chapter can only cost something the reader has already been shown."""
    numbers = {c.anchor: c.number for c in CHAPTERS}
    for anchor in chapter.answers:
        assert anchor in numbers, f"{chapter.label} names {anchor}, which is not a chapter"
        assert numbers[anchor] < chapter.number, (
            f"{chapter.label} claims to cost {anchor}, which comes later — the reader would "
            "meet the price before the mechanism"
        )


@pytest.mark.parametrize("chapter", PAIRED, ids=[c.label for c in PAIRED])
def test_pairing_is_in_the_chapter_header(chapter: Chapter):
    header = (ROOT / chapter.path).read_text()
    assert "| **Answers the cost of** |" in header, (
        f"{chapter.path} names a counterpart in the outline but its header does not say so — "
        "regenerate the stub, or add the row by hand if the chapter is written"
    )
    for anchor in chapter.answers:
        counterpart = next(c for c in CHAPTERS if c.anchor == anchor)
        assert f"[{counterpart.label}](#{anchor})" in header, (
            f"{chapter.path} omits {anchor} from its header"
        )


def test_every_part_three_chapter_either_pairs_or_is_deliberately_standalone():
    """Part V is Part IV re-asked as cost questions, so an unpaired chapter needs a reason.

    Three have one. ch21 teaches measurement itself and has no earlier counterpart; ch27 is about
    the whole machine rather than one mechanism; ch28 is about hardware Part IV never described.
    Anything else unpaired is an oversight, not a decision.

    ``PARTS[-1]`` rather than ``PARTS[2]``: the cost part was the third of three until Part I was
    added in front of it, at which point index 2 quietly became a different part and the test
    started reporting the toolchain chapters as unpaired. The last part is what this is about.
    """
    standalone = {"measuring", "whole-machine-profiling", "vectors"}
    unpaired = {
        chapter.label
        for chapter in CHAPTERS
        if chapter.part == PARTS[-1].title
        and not chapter.answers
        and chapter.anchor not in standalone
    }
    assert not unpaired, (
        f"these Part V chapters neither pair with an earlier chapter nor are listed as "
        f"deliberately standalone: {sorted(unpaired)}"
    )


@pytest.mark.parametrize("chapter", PAIRED, ids=[c.label for c in PAIRED])
def test_the_preface_shows_the_pairing(chapter: Chapter):
    """The preface promises the reader that Part V re-asks Part IV. The table must stay true.

    It lives in the preface rather than ch00 because it is an argument about how the book is
    built, which a reader needs before deciding to read it — where ch00 is about getting two
    machines working. ch20 is exempt: it crosses the seam rather than costing one mechanism, and
    the preface discusses it in prose instead.
    """
    if chapter.anchor == "the-same-program-on-both-targets":
        pytest.skip("ch20 is the crossing itself, not a row in the table")
    preface = (ROOT / "index.md").read_text()
    section = preface[preface.index("### One argument, not two tutorials") :]
    assert chapter.label in section, (
        f"{chapter.label} pairs with an earlier chapter but the preface's table omits it"
    )
    for label in chapter.answers:
        assert label in section, (
            f"the preface's table does not show that {chapter.label} costs {label}"
        )


# -- the claim about what the instruction-set split costs -----------------------------------

#: Every page that tells the reader how much AArch64 they are in for. Each states it at its own
#: length, and all of them have to name the same chapters.
DISASSEMBLY_CLAIMS = ("index.md", "README.md", "hardware/README.md")


def _labels_near(text: str, keyword: str) -> set[str]:
    """Chapter labels in the paragraph that mentions `keyword`."""
    paragraphs = [block for block in text.split("\n\n") if keyword in block]
    return {label for block in paragraphs for label in re.findall(r"\bch\d\d\b", block)}


@pytest.mark.parametrize("page", DISASSEMBLY_CLAIMS)
def test_pages_agree_on_which_chapters_read_disassembly(page: str):
    """Three pages make this claim, and they had already drifted into three different answers.

    It is load-bearing: it is the reason the two targets are allowed not to share an instruction
    set, so a reader deciding whether to accept that bargain is owed the real number. The outline
    is the source; this asserts each page tells the same story it does.

    Two rules, because the pages are not the same length. Every page must name the complete
    **AArch64** set, since that is the cost being claimed and an understatement of it is the
    failure that matters. No page may name a chapter that does not read disassembly at all.
    Naming the RISC-V side as well is optional — `hardware/README.md` is about Part V only.

    ch00 is excluded throughout: it *demonstrates* both rather than requiring either.
    """
    without_ch00 = lambda kind: {  # noqa: E731
        label for label in reading_disassembly(kind) if label != "ch00"
    }
    text = (ROOT / page).read_text()
    # ch00 comes off both sides, not just the outline's. It reads disassembly on both
    # architectures and is excluded from the *cost* being claimed, so a page naming it in this
    # paragraph — the preface points at it for exactly that reason — is telling the truth.
    found = _labels_near(text, "disassembly") - {"ch00"}
    assert found, f"{page} no longer says anything about reading disassembly"

    missing = without_ch00("aarch64") - found
    assert not missing, (
        f"{page} understates what the instruction-set split costs: it omits {sorted(missing)}"
    )
    wrong = found - without_ch00("aarch64") - without_ch00("riscv")
    assert not wrong, f"{page} says {sorted(wrong)} read disassembly; bench/outline.py disagrees"


def test_checkpoint_tags_match_the_outline():
    """CHECKPOINTS.md and the outline had disagreed about ch28 since Part V moved to AArch64.

    The chapter stopped being unmeasurable and started leaving code behind; PLAN.md was updated
    and the tag table was not. A reader following the tags would have looked for a checkpoint the
    book said did not exist.
    """
    table = (ROOT / "CHECKPOINTS.md").read_text()
    rows = dict(re.findall(r"^\|\s*(ch\d\d)\s*\|\s*(.*?)\s*\|", table, re.MULTILINE))
    for chapter in CHAPTERS:
        assert chapter.label in rows, f"CHECKPOINTS.md has no row for {chapter.label}"
        cell = rows[chapter.label]
        if chapter.tag is None:
            assert "`" not in cell, f"{chapter.label} has no tag in the outline but {cell!r} here"
        else:
            assert f"`{chapter.tag}`" in cell, (
                f"CHECKPOINTS.md gives {chapter.label} {cell!r}, the outline says {chapter.tag!r}"
            )


# -- what a stub is for --------------------------------------------------------------------


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_every_chapter_names_the_measurements_it_owes(chapter: Chapter):
    """The preface promises this, and for a while the promise was two-thirds kept.

    "Every other chapter is a stub carrying its target, its question and the measurements it owes
    you" — and the row said *[To write: the figure this chapter produces]*, identically, in all
    twenty-one of them. A stub that names its debt is useful to a reader deciding where to wait;
    one that names a placeholder is twenty-one identical pages behind twenty-one different titles.

    The debt is discharged when the chapter is written, so this applies to stubs only.
    """
    text = (ROOT / chapter.path).read_text()
    assert chapter.owes or chapter.number == 0, f"{chapter.label} has no `owes` in the outline"
    if "[DRAFT]" not in text:
        # A written chapter has discharged the debt: its header names the result files it
        # actually produced, which is more use to a reader than the promise it replaced.
        return
    header = text.split(":::", 2)[1]
    assert chapter.owes in header, (
        f"{chapter.label}'s header does not carry what the outline says it owes — "
        "regenerate with `python3 scripts/new-chapter.py --all --force`"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_no_chapter_owes_a_timing_to_the_wrong_target(chapter: Chapter):
    """An `xv6` chapter that promised a duration would be promising something CI must reject."""
    if chapter.target != "xv6" or not chapter.owes:
        return
    forbidden = ("nanosecond", "how long", "speedup", "latency", "throughput")
    found = [word for word in forbidden if word in chapter.owes.lower()]
    assert not found, (
        f"{chapter.label} is an xv6 chapter but says it owes {found} — "
        "QEMU cannot produce that, and bench.stamp would refuse to record it"
    )


APPENDIX_IDS = [appendix.letter for appendix in APPENDICES]


@pytest.mark.parametrize("appendix", APPENDICES, ids=APPENDIX_IDS)
def test_every_appendix_says_what_it_will_hold(appendix: Appendix):
    """Six appendices used to be one sentence repeated six times.

    Defensible in a template, indefensible as six published pages. Where the content comes from
    differs more than the titles suggest — a specification, the board, the submodule — and that is
    what decides when each one can be written at all.
    """
    assert appendix.holds and appendix.source, f"Appendix {appendix.letter} is undescribed"
    text = (ROOT / appendix.path).read_text()

    if "[DRAFT]" not in text:
        # The promise is discharged once the page exists, exactly as a written chapter's `owes`
        # row is. What replaces it is the stricter requirement: a page with its marker off must
        # not still be carrying the scaffolding a stub is made of.
        leftovers = [marker for marker in ("Not written yet", "[To write") if marker in text]
        assert not leftovers, (
            f"Appendix {appendix.letter} has lost its [DRAFT] marker but still contains {leftovers}"
        )
        return

    assert appendix.holds in text, f"Appendix {appendix.letter} does not say what it will hold"
    assert appendix.source in text, f"Appendix {appendix.letter} does not say where it comes from"


def test_the_appendices_are_not_all_the_same_page():
    """The check that would have caught it: six titles, six bodies, six different bodies."""
    bodies = {
        (ROOT / appendix.path).read_text().split("# Appendix", 1)[1] for appendix in APPENDICES
    }
    assert len(bodies) == len(APPENDICES), "two appendices are the same page under two titles"


def _verify_numbers_module():
    """Import the script by path. Its name has a hyphen in it, so `import` will not do."""
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location("vn", ROOT / "scripts" / "verify-numbers.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CAUGHT = [
    "the median was 120 ns",
    "it took 1.5 ms",
    "3.2x faster than before",
    "a 15% improvement",
    "83 instructions of trap path",
    "2,400 cycles",
]

#: Things that look like a figure to a careless regex and are not one. The vector arrangement
#: specifiers are the ones that actually got through: `v0.4s` contains `0.4s`, and appendix F is
#: made of them.
NOT_CAUGHT = [
    "`v0.4s` is four 32-bit lanes",
    "`movi v0.2s, #0` is how a float zero is made",
    "the `v0.16b` form",
    "register `x8` carries the call number",
    "Sv39 has three levels",
]


def test_the_typed_number_rule_catches_a_figure_and_not_a_register_name():
    """The guard on the guard, added when the rule reported a vector register as a duration.

    Both halves matter. A rule that stopped catching figures would let the book's whole premise
    quietly lapse; a rule that fires on `v0.4s` teaches an author to reach for the exemption
    comment, which is worse, because the exemption is meant to be rare enough to read.
    """
    pattern = _verify_numbers_module().MEASURED_FIGURE
    missed = [line for line in CAUGHT if not pattern.search(line)]
    assert not missed, f"a measured figure typed into prose would now go through: {missed}"
    spurious = {line: pattern.findall(line) for line in NOT_CAUGHT if pattern.search(line)}
    assert not spurious, f"not measurements, and reported as such: {spurious}"


def test_every_published_page_is_checked_for_typed_numbers():
    """The no-typed-numbers rule has to cover the book, not most of it.

    `verify-numbers.py` scanned `chapters/` and `appendices/` and not `index.md`, so the preface —
    the most-read page, and the one carrying a hardware comparison table — was the single page
    allowed to type a measurement into a sentence. A page added to the table of contents must not
    be able to land outside the check either, so the two lists are compared rather than trusted.
    """
    import subprocess  # noqa: PLC0415

    scanned = subprocess.run(
        [
            "python3",
            "-c",
            "import sys; sys.path.insert(0, '.'); "
            "sys.path.insert(0, 'scripts'); "
            "import importlib.util as u; "
            "s = u.spec_from_file_location('vn', 'scripts/verify-numbers.py'); "
            "m = u.module_from_spec(s); s.loader.exec_module(m); "
            "print('\\n'.join(str(p.relative_to(m.ROOT)) for p in m.published_pages()))",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    ).stdout.split()

    for page in ["index.md", *TOC_FILES]:
        assert page in scanned, f"{page} is published but verify-numbers.py never reads it"


# -- figures earn their place, and get used -------------------------------------------------

PAGES = ["index.md", *TOC_FILES]


def _all_page_text() -> str:
    return "\n".join((ROOT / page).read_text() for page in PAGES)


def test_every_declared_figure_is_included_somewhere():
    """A figure nobody includes is one the reader never sees, and CI still renders it forever.

    The mirror of the check that every included fragment exists. Both failures are silent: one
    leaves a hole in a chapter, the other leaves work in the repository doing nothing.
    """
    from bench.figures import FIGURES, Diagram  # noqa: PLC0415

    text = _all_page_text()
    orphans = []
    for name, figure in FIGURES.items():
        needle = f"_figures/{name}.svg" if isinstance(figure, Diagram) else f"_generated/{name}.md"
        if needle not in text:
            orphans.append(name)
    assert not orphans, f"declared but included by no page: {sorted(orphans)}"


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_a_written_chapter_shows_the_reader_something(chapter: Chapter):
    """Prose alone is not this book's format.

    CLAUDE.md §7 asks for figures that show a mechanism, and a finished chapter with nothing
    included from `bench/figures.py` has either measured nothing or drawn nothing — both of which
    are worth failing over rather than discovering at proof stage.
    """
    text = (ROOT / chapter.path).read_text()
    if "[DRAFT]" in text:
        return
    assert "_generated/" in text or "_figures/" in text, (
        f"{chapter.label} is finished but includes no table, listing or diagram"
    )


def test_ci_runs_nothing_a_contributor_cannot_run():
    """`make check` must be exactly what CI runs, or a check only fires after the push.

    It was not. `bench.run_setup --check` lived in the workflow alone, so six commits passed
    locally while CI was red on a result ch13's kernel patch had made stale. A check a
    contributor cannot run is one that reports at the worst possible moment, and it is worth a
    test rather than a convention because the drift is invisible: both files stay valid.

    Two commands are exempt. `verify-setup.py` is a record of what the runner can reach rather
    than a check — it is run with `|| true` — and `ci-check.sh` is the thing itself.
    """
    import yaml  # noqa: PLC0415

    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "quality.yml").read_text())
    allowed = ("verify-setup.py", "ci-check.sh")
    smuggled = [
        step.get("name", step["run"].strip().splitlines()[0])
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "run" in step
        and ("python3 -m bench." in step["run"] or "scripts/" in step["run"])
        and not any(permitted in step["run"] for permitted in allowed)
    ]
    assert not smuggled, (
        "these workflow steps check something scripts/ci-check.sh does not, so `make check` is "
        f"no longer what CI runs: {smuggled}"
    )
