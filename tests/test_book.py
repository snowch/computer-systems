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

from bench.outline import APPENDICES, CHAPTERS, PARTS, Appendix, Chapter, reading_disassembly
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
        # The heading, not the label anywhere in the file. A passing mention in another
        # chapter's entry — or in a footer saying which chapters are still stubs — used to
        # satisfy this, which is how ch23 briefly had no entry and a green test.
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
    prompt that dropped it would send someone to buy a board that cannot run Part IV.
    """
    text = PROMPT.read_text()
    for required in (
        "perf stat -e cycles,instructions",
        "<not supported>",
        "perf record",
    ):
        assert required in text, f"the board prompt no longer mentions {required!r}"


def test_the_board_prompt_keeps_the_riscv_warning():
    """Hard-won, and the reason Part IV is not on RISC-V. It must not be quietly dropped.

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

    chapter = (ROOT / "chapters" / "ch00_prerequisites_and_setup.md").read_text()
    assert "hardware/README.md" in chapter, "ch00 no longer points anywhere for the alternative"
    assert signature not in chapter, "ch00 has pasted the prompt"


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
    chapter = (ROOT / "chapters" / "ch00_prerequisites_and_setup.md").read_text()
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
    labels = {c.label: c.number for c in CHAPTERS}
    for label in chapter.answers:
        assert label in labels, f"{chapter.label} names {label}, which is not a chapter"
        assert labels[label] < chapter.number, (
            f"{chapter.label} claims to cost {label}, which comes later — the reader would meet "
            "the price before the mechanism"
        )


@pytest.mark.parametrize("chapter", PAIRED, ids=[c.label for c in PAIRED])
def test_pairing_is_in_the_chapter_header(chapter: Chapter):
    header = (ROOT / chapter.path).read_text()
    assert "| **Answers the cost of** |" in header, (
        f"{chapter.path} names a counterpart in the outline but its header does not say so — "
        "regenerate the stub, or add the row by hand if the chapter is written"
    )
    for label in chapter.answers:
        assert f"[{label}](#{label})" in header, f"{chapter.path} omits {label} from its header"


def test_every_part_three_chapter_either_pairs_or_is_deliberately_standalone():
    """Part IV is Part III re-asked as cost questions, so an unpaired chapter needs a reason.

    Three have one. ch16 teaches measurement itself and has no earlier counterpart; ch22 is about
    the whole machine rather than one mechanism; ch23 is about hardware Part III never described.
    Anything else unpaired is an oversight, not a decision.

    ``PARTS[-1]`` rather than ``PARTS[2]``: the cost part was the third of three until Part I was
    added in front of it, at which point index 2 quietly became a different part and the test
    started reporting the toolchain chapters as unpaired. The last part is what this is about.
    """
    standalone = {"ch16", "ch22", "ch23"}
    unpaired = {
        chapter.label
        for chapter in CHAPTERS
        if chapter.part == PARTS[-1] and not chapter.answers and chapter.label not in standalone
    }
    assert not unpaired, (
        f"these Part IV chapters neither pair with an earlier chapter nor are listed as "
        f"deliberately standalone: {sorted(unpaired)}"
    )


@pytest.mark.parametrize("chapter", PAIRED, ids=[c.label for c in PAIRED])
def test_the_preface_shows_the_pairing(chapter: Chapter):
    """The preface promises the reader that Part IV re-asks Part III. The table must stay true.

    It lives in the preface rather than ch00 because it is an argument about how the book is
    built, which a reader needs before deciding to read it — where ch00 is about getting two
    machines working. ch15 is exempt: it crosses the seam rather than costing one mechanism, and
    the preface discusses it in prose instead.
    """
    if chapter.label == "ch15":
        pytest.skip("ch15 is the crossing itself, not a row in the table")
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
    Naming the RISC-V side as well is optional — `hardware/README.md` is about Part IV only.

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
    """CHECKPOINTS.md and the outline had disagreed about ch23 since Part IV moved to AArch64.

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
    locally while CI was red on a result ch08's kernel patch had made stale. A check a
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
