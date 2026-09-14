"""The book's own structure: outline, table of contents and files on disk agree.

These are cheap and they catch the mistakes that cost the most time — a chapter renamed in one
place and not the other, a chapter whose header claims a target the plan does not give it, a
`{literalinclude}` anchored on a line number that will rot on the first edit above it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from bench.outline import APPENDICES, CHAPTERS, PARTS, Chapter
from bench.stamp import ROOT

MYST = yaml.safe_load((ROOT / "myst.yml").read_text())
TOC = MYST["project"]["toc"]
TOC_FILES = [child["file"] for entry in TOC if "children" in entry for child in entry["children"]]

CHAPTER_IDS = [chapter.label for chapter in CHAPTERS]


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
    expected = {"xv6": "`xv6`", "host": "`host`", "both": "`xv6` and `host`"}[chapter.target]
    assert expected in declared, (
        f"{chapter.path} declares {declared.strip()!r}, but the outline says {chapter.target!r}"
    )


@pytest.mark.parametrize("chapter", CHAPTERS, ids=CHAPTER_IDS)
def test_chapter_has_a_label_matching_its_number(chapter: Chapter):
    text = (ROOT / chapter.path).read_text()
    assert f"({chapter.label})=" in text, f"{chapter.path} needs a `({chapter.label})=` label"


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
    assert titles[: len(PARTS)] == list(PARTS)


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
        assert chapter.label in originality, (
            f"{chapter.label} has lost its [DRAFT] marker but ORIGINALITY.md does not cover it"
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
    prompt that dropped it would send someone to buy a board that cannot run Part III.
    """
    text = PROMPT.read_text()
    for required in (
        "perf stat -e cycles,instructions",
        "<not supported>",
        "SBI PMU",
        "CONFIG_RISCV_PMU_SBI",
        "rv64imafdc",
    ):
        assert required in text, f"the board prompt no longer mentions {required!r}"


def test_the_board_prompt_asks_for_sources_and_admits_uncertainty():
    """An LLM guessing confidently about perf support is the failure mode this guards against."""
    text = PROMPT.read_text().lower()
    assert "source" in text
    assert "unsure" in text or "uncertain" in text


def test_the_board_prompt_has_placeholders_to_fill_in():
    text = PROMPT.read_text()
    assert "[YOUR COUNTRY]" in text
    assert "[YOUR BUDGET]" in text


def test_chapter_zero_quotes_the_prompt_rather_than_copying_it():
    """One source of truth: ch00 literalincludes the file, it does not paste it."""
    chapter = (ROOT / "chapters" / "ch00_prerequisites_and_setup.md").read_text()
    assert "{literalinclude} ../hardware/find-a-board.txt" in chapter
    assert "hardware/README.md" in chapter


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
def test_chapter_zero_names_every_hardware_sensitive_chapter(chapter: Chapter):
    """ch00 promises a complete list. A chapter added later must not quietly escape it."""
    ch00 = (ROOT / "chapters" / "ch00_prerequisites_and_setup.md").read_text()
    section = ch00[ch00.index("### Which chapters actually depend on the hardware") :]
    assert f"[{chapter.label}](#{chapter.label})" in section, (
        f"{chapter.label} assumes something about the hardware but ch00's list omits it"
    )


def test_host_chapter_headers_do_not_name_a_specific_board():
    """The hardware requirement is a capability (ch00), so a header naming one board is wrong.

    Every host chapter said 'VisionFive 2 Lite' until this was caught — nine chapters that would
    have been inaccurate for any reader who bought something else.
    """
    offenders = []
    for chapter in CHAPTERS:
        if chapter.target != "host":
            continue
        header = (ROOT / chapter.path).read_text().split(":::", 2)[1]
        if re.search(r"VisionFive|StarFive|JH7110", header):
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
    chapter = (ROOT / "chapters" / "ch00_prerequisites_and_setup.md").read_text()
    for text, where in ((notes, "hardware/README.md"), (chapter, "ch00")):
        lowered = text.lower()
        assert "return policy" in lowered, f"{where} does not mention checking the return policy"
        assert "warranty" in lowered, f"{where} does not disclaim a warranty"
    assert "The purchase is yours and so is the risk" in notes
