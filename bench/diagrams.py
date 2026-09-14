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


def _svg(width: int, height: int, body: list[str], title: str) -> str:
    """Wrap the parts in a root element, with a title for anyone using a screen reader."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">\n'
        f"  <title>{escape(title)}</title>\n"
        f'  <rect width="{width}" height="{height}" fill="{PAPER}"/>\n  '
        + "\n  ".join(body)
        + "\n</svg>\n"
    )


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
