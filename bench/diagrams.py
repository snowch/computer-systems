"""Figures, drawn by code, as deterministic SVG.

Two rules, and the second explains the first.

**Every figure in this book is drawn by something in this file or is a table.** No screenshots,
and nothing traced from someone else's diagram (PLAN.md §5). A figure that cannot be regenerated
from source cannot be corrected when the thing it describes changes.

**The bytes are deterministic.** ``scripts/render-figures.py --check`` fails CI when a committed
figure no longer matches what the code produces, which is the same staleness guarantee the tables
get — and it only works if generating the same figure twice produces identical bytes. A plotting
library does not promise that: matplotlib embeds font paths and its own version, so the check
would fail on an upgrade that changed nothing a reader can see, and authors would learn to ignore
it. Hand-built SVG has no such problem, costs one small module, and prints properly.

The palette is fixed and light-background on purpose: an ``<img>`` cannot inherit the page's
colours, so a figure that assumed a dark theme would be unreadable in the PDF and vice versa.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

INK = "#1a1a1a"
MUTED = "#5b6270"
RULE = "#c9ced6"
PANEL = "#f6f7f9"
WARN = "#c2410c"
PAPER = "#ffffff"

SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Menlo, Consolas, monospace"


def _text(
    x: float,
    y: float,
    body: str,
    *,
    size: float = 13,
    fill: str = INK,
    weight: str = "normal",
    family: str = SANS,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(body)}</text>'
    )


def _rect(x: float, y: float, w: float, h: float, *, fill: str, stroke: str = RULE) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
    )


#: One arrowhead, defined once and referenced by every arrow. Inlined into each figure rather
#: than shared across files because an ``<img>`` is its own document: a marker defined elsewhere
#: does not exist as far as this SVG is concerned.
_DEFS = (
    '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
    'markerHeight="6" orient="auto-start-reverse">'
    f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{INK}"/></marker></defs>'
)


def _svg(width: int, height: int, body: list[str], title: str) -> str:
    """Wrap the parts in a root element, with a title for anyone using a screen reader."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">\n'
        f"  <title>{escape(title)}</title>\n"
        f"  {_DEFS}\n"
        f'  <rect width="{width}" height="{height}" fill="{PAPER}"/>\n  '
        + "\n  ".join(body)
        + "\n</svg>\n"
    )


# -- primitives -----------------------------------------------------------------------------
#
# Enough vocabulary to draw what a systems book needs, and no more. Four shapes recur across
# twenty-two chapters: a row of cells (bits, bytes, struct members, cache lines), a column of
# regions with addresses beside them (an address space, a stack frame, a page table), a chain of
# stages with arrows between them (a toolchain, a trap path, a pipeline), and free arrows for
# everything else. Building those once means a chapter's figure function says what the figure
# *is* rather than where its rectangles go.


def _line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = RULE, dash: str = "") -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}"{extra}/>'


def _arrow(x1: float, y1: float, x2: float, y2: float, *, stroke: str = INK) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
        f'stroke-width="1.4" marker-end="url(#a)"/>'
    )


def _mono(x: float, y: float, body: str, **kwargs) -> str:
    kwargs.setdefault("size", 11.5)
    return _text(x, y, body, family=MONO, **kwargs)


def cells(
    x: float,
    y: float,
    items: list[tuple[str, float]],
    *,
    height: float = 38,
    fill: str = PANEL,
    label_size: float = 12,
    mono: bool = True,
) -> tuple[list[str], float]:
    """A row of adjacent boxes, each given its own width. Returns the parts and the total width.

    Adjacent and not spaced, because in every use of this the thing being drawn *is* contiguous —
    bits in a word, bytes in a struct, blocks on a disk. A gap between the boxes would draw a
    space that is not there.
    """
    parts: list[str] = []
    cursor = x
    for label, width in items:
        parts.append(_rect(cursor, y, width, height, fill=fill))
        writer = _mono if mono else _text
        parts.append(
            writer(cursor + width / 2, y + height / 2 + 4, label, size=label_size, anchor="middle")
        )
        cursor += width
    return parts, cursor - x


def column(
    x: float,
    y: float,
    width: float,
    rows: list[tuple[str, str]],
    *,
    row_height: float = 34,
    fill: str = PANEL,
) -> tuple[list[str], float]:
    """A vertical stack of regions, each with a note to its right. Returns parts and total height.

    Drawn top-down in the order given. Address spaces are conventionally drawn with low addresses
    at the bottom, so a caller wanting that passes its rows already reversed — the function does
    not guess, because half the uses here are not address spaces.
    """
    parts: list[str] = []
    cursor = y
    for label, note in rows:
        parts.append(_rect(x, cursor, width, row_height, fill=fill))
        parts.append(_mono(x + 12, cursor + row_height / 2 + 4, label, size=12))
        if note:
            parts.append(
                _text(x + width + 14, cursor + row_height / 2 + 4, note, size=12, fill=MUTED)
            )
        cursor += row_height
    return parts, cursor - y


def chain(
    x: float,
    y: float,
    stages: list[tuple[str, str]],
    *,
    box_width: float = 118,
    box_height: float = 52,
    gap: float = 34,
) -> tuple[list[str], float]:
    """Boxes left to right with an arrow between each pair. Returns parts and total width.

    Each stage is a heading and one line under it. The arrows carry the meaning — this shape is
    for things that happen in an order, and the gap is where the reader should ask what the
    previous stage handed over.
    """
    parts: list[str] = []
    cursor = x
    for index, (heading, note) in enumerate(stages):
        if index:
            parts.append(
                _arrow(cursor - gap + 6, y + box_height / 2, cursor - 6, y + box_height / 2)
            )
        parts.append(_rect(cursor, y, box_width, box_height, fill=PANEL))
        parts.append(
            _text(cursor + box_width / 2, y + 22, heading, size=12.5, weight="700", anchor="middle")
        )
        parts.append(
            _text(cursor + box_width / 2, y + 39, note, size=11, fill=MUTED, anchor="middle")
        )
        cursor += box_width + gap
    return parts, cursor - x - gap


def heading(x: float, y: float, title: str, subtitle: str = "") -> list[str]:
    """Every figure opens the same way, so that a reader meeting the tenth one already knows."""
    parts = [_text(x, y, title, size=17, weight="700")]
    if subtitle:
        parts.append(_text(x, y + 20, subtitle, size=12.5, fill=MUTED))
    return parts


def footnote(x: float, y: float, width: float, lines: list[str]) -> list[str]:
    """The rule and the small print under a figure: what it is not saying."""
    parts = [_line(x, y - 22, x + width, y - 22)]
    for index, line in enumerate(lines):
        parts.append(_text(x, y + index * 18, line, size=12, fill=MUTED))
    return parts


def _panel(
    x: float,
    y: float,
    w: float,
    heading: str,
    subtitle: str,
    answers: list[str],
    silent_about: list[str],
) -> tuple[list[str], float]:
    """One target's column: what it answers, then what it has no opinion about."""
    parts: list[str] = []
    line_height = 21
    head_h = 52
    answers_h = head_h + 24 + line_height * len(answers) + 10
    silent_h = 26 + line_height * len(silent_about) + 12
    total = answers_h + silent_h + 12

    parts.append(_rect(x, y, w, total, fill=PANEL))
    parts.append(_text(x + 16, y + 28, heading, size=15, weight="700"))
    parts.append(_text(x + 16, y + 46, subtitle, size=12, fill=MUTED))
    parts.append(
        f'<line x1="{x}" y1="{y + head_h}" x2="{x + w}" y2="{y + head_h}" stroke="{RULE}"/>'
    )

    cursor = y + head_h + 26
    parts.append(_text(x + 16, cursor, "Answers, exactly", size=11, weight="700", fill=MUTED))
    for item in answers:
        cursor += line_height
        parts.append(_text(x + 16, cursor, f"• {item}", size=12.5))

    cursor += 30
    parts.append(
        f'<line x1="{x + 12}" y1="{cursor - 20}" x2="{x + w - 12}" y2="{cursor - 20}" '
        f'stroke="{RULE}" stroke-dasharray="3 3"/>'
    )
    parts.append(_text(x + 16, cursor - 2, "Cannot tell you", size=11, weight="700", fill=WARN))
    for item in silent_about:
        cursor += line_height
        parts.append(_text(x + 16, cursor, f"✗ {item}", size=12.5, fill=MUTED))

    return parts, total


def two_target_map() -> str:
    """The division of labour between the two targets, which is the shape of the whole book.

    Drawn rather than tabulated because the asymmetry is the content: each target has a list of
    things it is authoritative about and a list of things it will happily produce a plausible
    number for and be wrong. Putting those two lists next to each other is the figure.
    """
    width, margin, gap = 780, 24, 22
    panel_w = (width - 2 * margin - gap) / 2
    top = 68
    body: list[str] = []

    body.append(_text(margin, 30, "One book, two targets", size=17, weight="700"))
    body.append(
        _text(
            margin,
            50,
            "Different machines, and different instruction sets. The mechanisms transfer; the numbers do not.",
            size=12.5,
            fill=MUTED,
        )
    )

    left, left_h = _panel(
        margin,
        top,
        panel_w,
        "xv6 under QEMU",
        "target: xv6 — what the program does",
        [
            "which instructions run, in order",
            "what a system call does to a process",
            "how a page table is walked",
            "what exec does to an address space",
            "why a scheduler picked this thread",
        ],
        [
            "how many cycles anything took",
            "whether a load hit in cache",
            "whether a branch was predicted",
            "what memory latency is",
        ],
    )
    right, right_h = _panel(
        margin + panel_w + gap,
        top,
        panel_w,
        "Linux on real hardware",
        "target: host — what the program costs",
        [
            "cycles and instructions retired",
            "cache and TLB miss rates",
            "branch mispredictions",
            "where the time went, by sampling",
            "what four cores do to each other",
        ],
        [
            "the kernel source under a breakpoint",
            "a page table you can print",
            "a scheduler you can instrument freely",
            "an experiment you can repeat exactly",
        ],
    )
    body += left + right

    footer_y = top + max(left_h, right_h) + 34
    body.append(
        f'<line x1="{margin}" y1="{footer_y - 22}" x2="{width - margin}" y2="{footer_y - 22}" '
        f'stroke="{RULE}"/>'
    )
    body.append(
        _text(
            margin,
            footer_y,
            "QEMU is a functional emulator. It has no cache model, no branch predictor and no",
            size=12,
            fill=MUTED,
        )
    )
    body.append(
        _text(
            margin,
            footer_y + 18,
            "performance counters — so it will answer a timing question, and the answer will be fiction.",
            size=12,
            fill=MUTED,
        )
    )

    return _svg(
        width, int(footer_y + 40), body, "The two execution targets and what each can answer"
    )


#: fragment name -> the function that draws it
DIAGRAMS = {
    "ch00-targets": two_target_map,
}
