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


def toolchain_stages() -> str:
    """What each stage of the toolchain hands to the next, and what it threw away doing it.

    Drawn rather than tabulated because the *shape* is the lesson: a reader who has only ever
    typed `gcc a.c -o a` believes in one box, and four boxes with arrows between them is the
    correction. The sizes live in a table underneath, from a stamped result; this figure says
    what each stage is *for*, which is the part that does not change between machines.
    """
    margin, top, width = 24, 24, 780
    body = heading(
        margin,
        top + 12,
        "One command, four programs",
        "`gcc a.c -o a` runs all of these. Each one hands the next a file you may look at.",
    )

    stages = [
        ("cpp", "preprocess"),
        ("cc1", "compile"),
        ("as", "assemble"),
        ("ld", "link"),
    ]
    row_y = top + 46
    parts, chain_width = chain(margin, row_y, stages, box_width=142, box_height=46, gap=44)
    body += parts

    # What arrives, under each arrow. The handover is the content: every one of these is a file
    # on disk that the next stage reads, and naming them is most of the chapter.
    handovers = [
        (".c", "text you wrote"),
        (".i", "text, includes pasted in"),
        (".s", "assembly, decisions made"),
        (".o", "bytes, plus holes to fill"),
        ("a.out", "bytes, no holes left"),
    ]
    label_y = row_y + 72
    step = 142 + 44
    for index, (name, note) in enumerate(handovers):
        x = margin + index * step - (22 if index else 0)
        body.append(_mono(x, label_y, name, size=12.5, weight="700"))
        body.append(_text(x, label_y + 17, note, size=11, fill=MUTED))

    # What each stage discards, which is the half nobody draws.
    discard_y = label_y + 56
    body.append(
        _text(margin, discard_y, "and what it throws away", size=11, weight="700", fill=WARN)
    )
    discards = [
        "comments, macro names",
        "types, names, most of the header",
        "mnemonics, whitespace",
        "nothing — it adds",
    ]
    for index, note in enumerate(discards):
        body.append(
            _text(margin + index * step, discard_y + 20, f"✗ {note}", size=11.5, fill=MUTED)
        )

    foot_y = discard_y + 62
    body += footnote(
        margin,
        foot_y,
        width - 2 * margin,
        [
            "Only the second box makes decisions. The first is text substitution, the third is a",
            "lookup table, and the fourth resolves addresses — none of them can change your loop.",
        ],
    )
    return _svg(
        width, int(foot_y + 30), body, "The four stages of the toolchain, and what each discards"
    )


def struct_padding(result: str) -> str:
    """Where the holes are, drawn from the offsets the probe measured rather than from the rules.

    ch00 prints a table saying one struct is larger than the other. A table cannot show *where*
    the extra bytes went, and that is the whole lesson: the gaps are not at the end, they are
    wedged between members, put there so the next member can start somewhere it is allowed to.

    Every offset below comes out of a stamped result, so this figure cannot drift away from the
    measurement it illustrates — and on an ABI that lays these out differently, it redraws.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    summary = load_result(result)["summary"]
    layouts = {entry["name"]: entry for entry in summary["layouts"]}
    offsets = summary["offsets"]

    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "Two structs, the same three members",
        "Declared in a different order, and one of them pays for it.",
    )

    # The two layouts, as the machine reported them. `first` is always at zero — a struct's first
    # member is, by definition — and the other two were measured.
    plans = [
        (
            "struct sysfs_declaration_order",
            "char first; int middle; char last;",
            layouts["declaration_order"],
            [
                ("first", 0, 1),
                ("middle", offsets["declaration_order.middle"], 4),
                ("last", offsets["declaration_order.last"], 1),
            ],
        ),
        (
            "struct sysfs_size_order",
            "int middle; char first; char last;",
            layouts["size_order"],
            [
                ("middle", 0, 4),
                ("first", offsets["size_order.first"], 1),
                ("last", offsets["size_order.last"], 1),
            ],
        ),
    ]

    cell = 42
    y = margin + 56
    for title, declaration, layout, members in plans:
        body.append(_text(margin, y, title, size=13, weight="700", family=MONO))
        body.append(_text(margin + 330, y, declaration, size=11.5, fill=MUTED, family=MONO))

        # One cell per byte. Bytes no member claims are holes, and they are what the figure is for.
        claimed: dict[int, str] = {}
        for name, offset, size in members:
            for step in range(size):
                claimed[offset + step] = name if step == 0 else "…"

        row: list[tuple[str, float]] = []
        for index in range(layout["size"]):
            row.append((claimed.get(index, "·"), cell))
        parts, _ = cells(margin, y + 14, row, height=34, label_size=10.5)
        body += parts

        for index in range(layout["size"]):
            body.append(
                _text(
                    margin + index * cell + cell / 2,
                    y + 62,
                    str(index),
                    size=10,
                    fill=MUTED,
                    anchor="middle",
                )
            )
        body.append(
            _text(
                margin + layout["size"] * cell + 16,
                y + 36,
                f"{layout['size']} bytes, {layout['padding']} of them holes",
                size=12,
                fill=WARN if layout["padding"] else MUTED,
            )
        )
        y += 104

    body.append(_text(margin, y, "·  a byte no member uses", size=11.5, fill=MUTED))
    foot = y + 46
    body += footnote(
        margin,
        foot,
        width - 2 * margin,
        [
            "Two rules produce every gap: a member starts at a multiple of its own alignment, and",
            "a struct is a multiple of its widest member's. The compiler may not reorder members to",
            "avoid either — C forbids it — so the order you wrote is the order you pay for.",
        ],
    )
    return _svg(
        width, int(foot + 48), body, "Where the padding goes in two orderings of the same struct"
    )


def dispatch_table() -> str:
    """An array of function pointers, and what an indirect call actually does.

    The pattern ch03 exists to teach and ch09 relies on: a kernel that must do *something*
    different for each of several devices does not write a switch, it writes a table and indexes
    it. Drawn because the mechanism is two dereferences — one to fetch the address, one to jump to
    it — and a sentence describing that is worth much less than a picture of it.
    """
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "A table of function pointers",
        "How a kernel does something different per device without knowing the devices.",
    )

    # The table: one slot per operation, each holding an address rather than code.
    slot = 116
    table_y = margin + 60
    names = ["ops[0]", "ops[1]", "ops[2]", "ops[3]"]
    parts, _ = cells(margin, table_y, [(name, slot) for name in names], height=42)
    body += parts
    body.append(
        _text(margin, table_y - 10, "the table, in memory", size=11, weight="700", fill=MUTED)
    )
    body.append(
        _text(
            margin + 4 * slot + 18, table_y + 26, "each slot holds an address,", size=12, fill=MUTED
        )
    )
    body.append(_text(margin + 4 * slot + 18, table_y + 43, "not a function", size=12, fill=MUTED))

    # The code each slot names, sitting somewhere else entirely.
    code_y = table_y + 118
    targets = ["read()", "write()", "ioctl()", "close()"]
    parts, _ = cells(margin, code_y, [(name, slot) for name in targets], height=42, mono=True)
    body += parts
    body.append(
        _text(margin, code_y - 10, "the code, elsewhere", size=11, weight="700", fill=MUTED)
    )

    for index in range(4):
        x = margin + index * slot + slot / 2
        body.append(_arrow(x, table_y + 46, x, code_y - 4))

    # The call itself, spelled out as the two steps it is.
    call_y = code_y + 92
    body.append(_mono(margin, call_y, "ops[n](arg)", size=13, weight="700"))
    body.append(
        _text(
            margin + 116,
            call_y,
            "1. load the address out of slot n     2. jump to whatever that was",
            size=12,
            fill=MUTED,
        )
    )

    foot = call_y + 50
    body += footnote(
        margin,
        foot,
        width - 2 * margin,
        [
            "A direct call names its target inside the instruction; the CPU knows where it is going",
            "before it fetches the operand. An indirect call does not, and ch17 measures what the",
            "branch predictor makes of that difference.",
        ],
    )
    return _svg(
        width,
        int(foot + 48),
        body,
        "A dispatch table of function pointers, and the two steps of an indirect call",
    )


def stack_frame() -> str:
    """One frame, and the two slots that make the frames into a list you can walk.

    Drawn because `sysfs/tools/framewalk.c` indexes those slots by number and a reader is owed a
    picture of what it is indexing. The addresses decrease upwards, which is the way the stack
    actually grows and the opposite of how a list is usually drawn — getting that backwards is
    most of why the subtraction in a prologue looks wrong the first time.
    """
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "A stack frame, and how to leave it",
        "Two fixed slots turn the frames into a linked list, which is all a backtrace is.",
    )

    box = 320
    top = margin + 62
    rows = [
        ("caller's frame", ""),
        ("saved fp  (fp-16)", "where the caller's frame begins"),
        ("return address  (fp-8)", "where to resume when this returns"),
        ("locals, spills, outgoing args", "whatever would not fit in registers"),
    ]
    parts, height = column(margin + 150, top, box, rows, row_height=46)
    body += parts

    # The two pointers, named where they actually point.
    fp_y = top + 46
    body.append(_mono(margin, fp_y + 8, "fp →", size=13, weight="700"))
    body.append(_text(margin, fp_y + 26, "this frame", size=11, fill=MUTED))
    sp_y = top + height
    body.append(_mono(margin, sp_y, "sp →", size=13, weight="700"))
    body.append(_text(margin, sp_y + 18, "the bottom", size=11, fill=MUTED))

    # Which way memory runs. Drawn because it is the thing readers get backwards.
    axis = margin + 150 + box + 54
    body.append(_arrow(axis, top + height - 8, axis, top + 8))
    body.append(_text(axis + 12, top + height / 2 - 6, "addresses", size=11, fill=MUTED))
    body.append(_text(axis + 12, top + height / 2 + 10, "increase", size=11, fill=MUTED))
    body.append(_text(axis + 12, top + height / 2 + 32, "the stack grows down", size=11, fill=WARN))

    # The walk itself, which is a two-line loop once the picture is in front of you.
    walk_y = top + height + 46
    body.append(_text(margin, walk_y, "to climb one frame", size=11, weight="700", fill=MUTED))
    body.append(_mono(margin, walk_y + 22, "return_address = fp[-1]", size=12))
    body.append(_mono(margin, walk_y + 42, "fp             = fp[-2]", size=12))

    foot = walk_y + 92
    body += footnote(
        margin,
        foot,
        width - 2 * margin,
        [
            "Only while frame pointers are kept. Compiled without them the slots are not written,",
            "the list does not exist, and a backtrace has to be reconstructed from debug tables",
            "instead — which is why a release build's stack trace is so often a disappointment.",
        ],
    )
    return _svg(
        width, int(foot + 48), body, "A RISC-V stack frame and the two slots a backtrace walks"
    )


def sections_to_segments(result: str) -> str:
    """Eighteen sections become two segments, and one of them is partly not in the file.

    The figure ch05 is for. Sections are the linker's view and segments are the loader's, the same
    bytes described twice for two audiences, and the collapse from one to the other is where a
    reader stops thinking of an executable as a list of named parts and starts thinking of it as
    an address space. Everything here is read from the stamped result.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    program = load_result(result)["summary"]["programs"]["sameanswer"]
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "Two views of the same bytes",
        "Sections are for the linker. Segments are for whatever has to load the thing.",
    )

    # Left: the sections that occupy memory, which is the short list. A reader who has just run
    # elfdump has seen the long one and the difference is the point.
    loaded = [s for s in program["sections"] if s["flags"] & 0x2]
    top = margin + 62
    rows = [(s["name"], f"{s['size']} bytes") for s in loaded]
    parts, sections_height = column(margin, top, 250, rows, row_height=34)
    body += parts
    body.append(
        _text(
            margin,
            top - 10,
            f"{len(program['sections'])} sections, {len(rows)} of them loaded",
            size=11,
            weight="700",
            fill=MUTED,
        )
    )

    # Right: the segments, drawn to the same scale of importance rather than of size.
    seg_x = margin + 430
    labels = {5: "r-x  code", 6: "rw-  data", 4: "r--  read only"}
    seg_rows = []
    for segment in program["segments"]:
        note = f"at {segment['vaddr']}"
        if segment["memory_bytes"] > segment["file_bytes"]:
            note += f"  ({segment['memory_bytes'] - segment['file_bytes']} bytes not in the file)"
        seg_rows.append((labels.get(segment["flags"], str(segment["flags"])), note))
    parts, _ = column(seg_x, top, 200, seg_rows, row_height=52)
    body += parts
    body.append(
        _text(
            seg_x,
            top - 10,
            f"{len(program['segments'])} segments",
            size=11,
            weight="700",
            fill=MUTED,
        )
    )

    for index in range(len(seg_rows)):
        body.append(
            _arrow(margin + 262, top + sections_height / 2, seg_x - 8, top + 26 + index * 52)
        )

    note_y = top + max(sections_height, len(seg_rows) * 52) + 40
    body.append(
        _text(
            margin,
            note_y,
            "the loader is told: map this much, from here, and zero the rest",
            size=12,
            fill=MUTED,
        )
    )

    foot = note_y + 54
    body += footnote(
        margin,
        foot,
        width - 2 * margin,
        [
            "A segment whose memory size exceeds its file size is asking for space that is not in",
            "the file: .bss. Storing a megabyte of zeroes would be silly, so the format says how",
            "many there are and the loader provides them.",
        ],
    )
    return _svg(
        width, int(foot + 48), body, "How an executable's sections collapse into loadable segments"
    )


def trap_path(result: str) -> str:
    """One system call, from the instruction that causes it to the instruction after it.

    Drawn because the shape is the argument: a call into the kernel is not a call. It is a
    hardware event, a page-table change, and two blocks of state movement wrapped around the work
    you actually asked for — and the work is the small box in the middle.

    The counts come from the stamped result, so the figure cannot claim a path length the
    measurement does not support.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    path = load_result(result)["summary"]["path"]
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "What one system call actually costs to arrange",
        "The work you asked for is the box in the middle. Everything else is getting there.",
    )

    stages = [
        ("ecall", "hardware traps"),
        ("uservec", f"save {path['uservec']['register_stores']} registers"),
        ("usertrap", "decide why"),
        ("syscall", "do the work"),
        ("userret", f"restore {path['userret']['register_loads']}"),
        ("sret", "back to user"),
    ]
    row_y = margin + 60
    parts, _ = chain(margin, row_y, stages, box_width=108, box_height=50, gap=18)
    body += parts

    # The part that is easy to miss and impossible to ignore once seen.
    note_y = row_y + 84
    body.append(
        _text(
            margin,
            note_y,
            "and twice, in the middle of it, the address space changes",
            size=12.5,
            weight="700",
            fill=WARN,
        )
    )
    body.append(
        _text(
            margin,
            note_y + 20,
            "uservec switches to the kernel page table; userret switches back. That is why both",
            size=12,
            fill=MUTED,
        )
    )
    body.append(
        _text(
            margin,
            note_y + 38,
            "halves live in one page mapped at the same address in both — the trampoline.",
            size=12,
            fill=MUTED,
        )
    )

    # The two blocks of state movement, side by side, because the symmetry is the point.
    bar_y = note_y + 76
    total = path["uservec"]["instructions"] + path["userret"]["instructions"]
    rows = [
        (f"uservec  {path['uservec']['instructions']} instructions", "in"),
        (f"userret  {path['userret']['instructions']} instructions", "out"),
    ]
    parts, height = column(margin, bar_y, 300, rows, row_height=34)
    body += parts
    body.append(
        _text(margin + 340, bar_y + 38, f"{total} instructions of pure state movement,", size=12.5)
    )
    body.append(
        _text(margin + 340, bar_y + 58, "before any of your work begins", size=12.5, fill=MUTED)
    )

    foot = bar_y + height + 58
    body += footnote(
        margin,
        foot,
        width - 2 * margin,
        [
            "Counted, not timed. This target cannot say what an instruction costs, and a count is",
            "what remains true anyway: the path is this long whatever machine runs it. ch19 prices",
            "the same shape on hardware.",
        ],
    )
    return _svg(width, int(foot + 48), body, "The path of one system call into the kernel and back")


def sv39_walk(result: str) -> str:
    """One virtual address, taken apart into the four things translation does with it.

    Drawn because the split is the mechanism and a sentence describing it is not memorable. Three
    nine-bit indices and a twelve-bit offset, each pointing at the level that consumes it — and
    the twenty-five bits at the top, which translation never looks at and which must therefore
    agree with bit 38 or the address is not an address.

    The spans come from the stamped result, so the figure cannot claim a geometry the model and
    the kernel have not agreed on.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    sv39 = load_result(result)["summary"]["sv39"]
    spans = sv39["spans"]
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "How Sv39 reads a virtual address",
        "Nine bits per level, three levels, and twelve bits it never touches.",
    )

    # Bit widths, drawn to scale: the unused quarter is genuinely a third of the word.
    bits = [
        ("63:39 — copies bit 38", 25),
        ("L2", 9),
        ("L1", 9),
        ("L0", 9),
        ("offset", 12),
    ]
    scale = (width - 2 * margin) / sum(count for _, count in bits)
    row_y = margin + 58
    parts, _ = cells(margin, row_y, [(label, count * scale) for label, count in bits], height=40)
    body += parts

    # Each index names the table that consumes it, and what one of its entries covers.
    levels = [
        ("L2", "root table", spans["2"]),
        ("L1", "second table", spans["1"]),
        ("L0", "third table", spans["0"]),
    ]
    box_w, gap = 176, 24
    table_y = row_y + 116
    cursor = margin + 96
    index_x = margin + 25 * scale
    for name, role, span in levels:
        body.append(_rect(cursor, table_y, box_w, 74, fill=PANEL))
        body.append(_text(cursor + 14, table_y + 26, role, size=13, weight="700"))
        body.append(_mono(cursor + 14, table_y + 46, f"{sv39['entries_per_table']} entries"))
        body.append(
            _text(
                cursor + 14, table_y + 64, f"one entry covers {_bytes(span)}", size=11.5, fill=MUTED
            )
        )
        body.append(_arrow(index_x + 4.5 * scale, row_y + 40, cursor + box_w / 2, table_y - 4))
        body.append(_mono(index_x + 4.5 * scale, row_y + 58, name, anchor="middle", fill=MUTED))
        index_x += 9 * scale
        cursor += box_w + gap

    note_y = table_y + 108
    body.append(
        _text(
            margin,
            note_y,
            "The offset is not translated. It is copied.",
            size=13.5,
            weight="700",
        )
    )
    body += footnote(
        margin,
        note_y + 42,
        width - 2 * margin,
        [
            f"Why nine: a {sv39['page_bytes']}-byte page holds {sv39['entries_per_table']} entries "
            f"of {sv39['entry_bytes']} bytes, and {sv39['entries_per_table']} is nine bits.",
            "Three levels of nine, plus twelve of offset, is thirty-nine — which is where the name comes from.",
        ],
    )
    return _svg(width, note_y + 92, body, "Sv39 address translation")


def _bytes(count: int) -> str:
    """Byte counts as a reader says them, for figure labels only."""
    for unit, size in (("GiB", 1 << 30), ("MiB", 1 << 20), ("KiB", 1 << 10)):
        if count >= size:
            return f"{count // size} {unit}"
    return f"{count} B"


def address_space_cost(result: str) -> str:
    """Why the smallest address space in the system has the worst overhead.

    The totals in the table next to this figure are not explicable without it. init maps six
    pages, and they are not in one place: four at the bottom of the address space and two at the
    very top. Each cluster forces its own chain down from the root, and a chain is two pages
    whether it ends in one mapping or five hundred.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    tables = load_result(result)["summary"]["tables"]
    init, kernel = tables["init"], tables["kernel"]
    runs = init["runs"]
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "A page table's size is decided by where the pages are",
        "init's address space: six mapped pages, five pages of table to describe them.",
    )

    # The virtual address space as one rule, with the two clusters marked where they fall.
    line_y = margin + 78
    left, right = margin + 10, width - margin - 10
    body.append(_line(left, line_y, right, line_y))
    body.append(_text(left, line_y + 26, "0", size=11.5, fill=MUTED, family=MONO))
    body.append(
        _text(right, line_y + 26, "MAXVA", size=11.5, fill=MUTED, anchor="end", family=MONO)
    )

    marks = []
    for index, run in enumerate(runs):
        at = left if index == 0 else right - 26
        body.append(_rect(at, line_y - 15, 26, 30, fill=PANEL))
        body.append(_mono(at + 13, line_y + 5, str(run["pages"]), anchor="middle"))
        marks.append((at + 13, f"{run['pages']} pages at {run['start']:#x}"))

    # Under each cluster, the chain of tables it forces. The root is shared; nothing else is.
    chain_y = line_y + 66
    box_w = 176
    for at, label in marks:
        # The clusters sit at the two ends of the address space, so their boxes have to be
        # pulled back inside the canvas; the arrow keeps them attached to the mark they explain.
        box_x = min(max(at - box_w / 2, margin), width - margin - box_w)
        centre = box_x + box_w / 2
        anchor = "start" if at < width / 2 else "end"
        text_x = box_x if anchor == "start" else box_x + box_w
        body.append(_text(text_x, chain_y - 14, label, size=11.5, fill=MUTED, anchor=anchor))
        for step, name in enumerate(("its own L1 table", "its own L0 table")):
            top = chain_y + step * 40
            body.append(_rect(box_x, top, box_w, 32, fill=PANEL))
            body.append(_text(centre, top + 21, name, size=12, anchor="middle"))
        body.append(_arrow(at, line_y + 18, centre, chain_y - 4))

    shared_y = chain_y + 96
    body.append(_rect(width / 2 - 88, shared_y, 176, 32, fill=PANEL))
    body.append(_text(width / 2, shared_y + 21, "one shared root", size=12, anchor="middle"))

    total = sum(init["table_pages"])
    verdict_y = shared_y + 76
    body.append(
        _text(
            margin,
            verdict_y,
            f"{total} pages of table for {init['leaf_entries'][0]} pages of memory.",
            size=13.5,
            weight="700",
        )
    )
    body += footnote(
        margin,
        verdict_y + 42,
        width - 2 * margin,
        [
            f"The kernel maps {kernel['leaf_entries'][0]} pages in {sum(kernel['table_pages'])} "
            "pages of table, because almost all of them are consecutive.",
            "Same mechanism, opposite result: the cost is per region, not per page.",
        ],
    )
    return _svg(width, verdict_y + 92, body, "What an address space costs to describe")


def fault_decision(result: str) -> str:
    """What the kernel does with a fault, and the one question that decides it.

    Drawn because the shape is the argument. A page fault is not an error report; it is the
    hardware calling a function of the kernel's choosing at the exact moment a particular address
    is touched, and handing it the address. Everything interesting that is built on faults is
    built by changing the test in the middle box.

    The counts come from the stamped result, so the figure cannot claim a workload the
    measurement does not support.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    run = load_result(result)["summary"]["faultload"]
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "A page fault is a question the kernel gets to answer",
        "The hardware supplies the address. What happens next is entirely policy.",
    )

    stages = [
        ("touch", "a load or a store"),
        ("fault", "walk stopped"),
        ("stval", "the address"),
        ("below sz?", "the only test"),
    ]
    row_y = margin + 62
    parts, _ = chain(margin, row_y, stages, box_width=142, box_height=52, gap=26)
    body += parts

    # The two answers, and what each costs in this run.
    branch_y = row_y + 112
    outcomes = [
        (
            "yes",
            "allocate a page, map it, and re-run the instruction that faulted",
            f"{run['lazy_pages']} pages this run",
        ),
        (
            "no",
            "the process asked for an address it never requested: kill it",
            f"{run['refused']} this run",
        ),
    ]
    box_w = (width - 2 * margin - 28) / 2
    for index, (answer, what, count) in enumerate(outcomes):
        box_x = margin + index * (box_w + 28)
        body.append(_rect(box_x, branch_y, box_w, 92, fill=PANEL))
        body.append(_text(box_x + 16, branch_y + 28, answer, size=14, weight="700"))
        body.append(_text(box_x + 16, branch_y + 52, what, size=12, fill=MUTED))
        body.append(_mono(box_x + 16, branch_y + 76, count))
        body.append(_arrow(margin + 3 * 168 + 71, row_y + 52, box_x + box_w / 2, branch_y - 4))

    note_y = branch_y + 132
    body.append(
        _text(
            margin,
            note_y,
            "Unlike a system call, the faulting instruction runs again.",
            size=13.5,
            weight="700",
        )
    )
    body += footnote(
        margin,
        note_y + 42,
        width - 2 * margin,
        [
            "Change the test and you get a different feature from the same hook: copy-on-write, a "
            "guard page, a page fetched from disk.",
            "This chapter measures one of them. The others are named in the text and not "
            "measured, which is not the same as being free.",
        ],
    )
    return _svg(width, note_y + 92, body, "What a kernel does with a page fault")


def interrupt_sources(result: str) -> str:
    """Where interrupts come from, and which of them a workload decides the number of.

    Drawn rather than tabulated because the asymmetry is the whole content, and a table with an
    empty cell in it invites the reader to think a number is merely missing. Two of these three
    sources produce counts this book will not print, and the figure says which and why on the
    face of it.
    """
    from bench.stamp import load_result  # noqa: PLC0415

    run = load_result(result)["summary"]["intrload"]
    margin, width = 24, 780
    body = heading(
        margin,
        margin + 12,
        "Three sources, and only one countable answer",
        "The work was fixed. Whether the interrupt count was fixed too depends on the device.",
    )

    sources = [
        (
            "Disk",
            "one completion per request",
            f"{run['disk_interrupts']} interrupts, every run",
            True,
        ),
        (
            "Console",
            "\u201cready for more\u201d, whenever that is",
            "a different number every run",
            False,
        ),
        (
            "Timer",
            "once per tick of elapsed time",
            "a fact about the host, not the guest",
            False,
        ),
    ]
    box_w = (width - 2 * margin - 2 * 20) / 3
    row_y = margin + 62
    for index, (title, mechanism, verdict, countable) in enumerate(sources):
        box_x = margin + index * (box_w + 20)
        body.append(_rect(box_x, row_y, box_w, 132, fill=PANEL))
        body.append(_text(box_x + 16, row_y + 30, title, size=15, weight="700"))
        body.append(_text(box_x + 16, row_y + 54, mechanism, size=11.5, fill=MUTED))
        body.append(_line(box_x + 12, row_y + 72, box_x + box_w - 12, row_y + 72, dash="3 3"))
        body.append(
            _text(
                box_x + 16,
                row_y + 94,
                "recorded" if countable else "not recorded",
                size=11,
                weight="700",
                fill=INK if countable else WARN,
            )
        )
        body.append(_text(box_x + 16, row_y + 114, verdict, size=11.5, fill=MUTED))

    note_y = row_y + 190
    body.append(
        _text(
            margin,
            note_y,
            "A block request is completed once. \u201cReady for more\u201d is not a unit of anything.",
            size=13.5,
            weight="700",
        )
    )
    body += footnote(
        margin,
        note_y + 42,
        width - 2 * margin,
        [
            "Same image, same workload: the disk count was identical on every run and the console "
            "count was not, over a spread of nearly a third.",
            "So one of these is a property of the work and the other is a property of the "
            "afternoon, and only one of them belongs in a table.",
        ],
    )
    return _svg(width, note_y + 92, body, "Where interrupts come from")


#: fragment name -> the function that draws it
DIAGRAMS = {
    "ch00-targets": two_target_map,
    "ch01-stages": toolchain_stages,
    "ch02-padding": struct_padding,
    "ch03-dispatch": dispatch_table,
    "ch04-frame": stack_frame,
    "ch05-segments": sections_to_segments,
    "ch06-trap-path": trap_path,
    "ch07-walk": sv39_walk,
    "ch07-address-spaces": address_space_cost,
    "ch08-decision": fault_decision,
    "ch09-sources": interrupt_sources,
}
