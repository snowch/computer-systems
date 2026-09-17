#!/usr/bin/env python3
"""The site's icon, drawn by code, and the files a phone needs in order to show it.

The mark is the book's own measurement: the latency curve of ch25 — flat, a step, flat, a step —
with the riser that costs in the accent colour. It is built from the palette in
``bench/diagrams.py`` so the tab icon and the diagrams are recognisably one thing.

**Why a script and not a checked-in drawing.** A figure that cannot be regenerated from source
cannot be corrected when the thing it describes changes (PLAN.md §5). An icon is site chrome
rather than a figure, but the argument is the same, and a binary dropped into the repository is
the one asset nobody can edit.

**Why it rasterises itself instead of driving a browser.** The first version screenshotted the
SVG in headless Chromium, and every PNG came out with a white band along the bottom: in current
Chromium ``--window-size`` is the *window*, not the viewport, and ``--headless=old`` — which
sized them the same — was removed. The icon had already been written and committed before anyone
looked at it at full size.

The mark is a union of axis-aligned rectangles, so the fix was to stop asking. Pixel coverage of
an axis-aligned rectangle is the product of two one-dimensional overlaps, which is exact
arithmetic rather than a rendering, needs nothing outside the standard library, and gives
byte-identical output on every machine. That last property is what lets ``--check`` compare every
pixel rather than trusting a file's dimensions — the same reasoning that keeps this book's
figures as hand-built SVG rather than a plotting library's output.

Usage::

    python3 scripts/make-icons.py            # write the SVG, the PNGs, the ICO and the manifest
    python3 scripts/make-icons.py --check    # verify every committed pixel
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "icons"

# The figure palette. Repeated here rather than imported from bench/diagrams.py because bench/
# is the measurement package and an icon is not a measurement; tests/test_book.py checks the two
# have not drifted.
INK = "#1a1a1a"
PAPER = "#ffffff"
ACCENT = "#c2410c"

#: The tile is opaque on purpose. iOS composites a transparent apple-touch-icon onto black, and
#: Android masks it against whatever the launcher likes, so an icon that carries its own
#: background is the only one that looks the same in both.
BACKGROUND = INK

#: The drawing, on a 64-unit grid, as ``(x0, y0, x1, y1, colour)``.
#:
#: Three equal treads and two equal risers, so it reads as a measurement rather than as a
#: decorative zigzag, and each segment is extended by half a stroke width at a corner so the
#: joins come out square. The mark spans x 8–56 and y 11–53, centred on (32, 32) both ways.
#: Later rectangles paint over earlier ones, which is how the accent claims the last riser and
#: the tread above it.
RECTS: tuple[tuple[float, float, float, float, str], ...] = (
    (8, 43, 29, 53, PAPER),
    (19, 27, 29, 53, PAPER),
    (19, 27, 45, 37, PAPER),
    (35, 11, 45, 37, PAPER),
    (35, 11, 56, 21, PAPER),
    (35, 11, 45, 37, ACCENT),
    (35, 11, 56, 21, ACCENT),
)

GRID = 64.0

#: name -> (pixel size, inset). The inset is the whole difference between a maskable icon and an
#: ordinary one: Android may crop to a circle of 80% diameter, and this mark's corners sit
#: outside it — (24, 16) from the centre is 28.8 units out, where the safe radius is 25.6.
RASTERS: dict[str, tuple[int, float]] = {
    "apple-touch-icon.png": (180, 0.0),
    "icon-192.png": (192, 0.0),
    "icon-512.png": (512, 0.0),
    "icon-maskable-512.png": (512, 0.18),
}

#: The sizes inside favicon.ico: 16 for a browser tab, 32 for a retina tab and most bookmark
#: lists, 48 for a pinned shortcut on Windows.
ICO_SIZES = (16, 32, 48)


# -- the drawing ------------------------------------------------------------------------------


def scaled(inset: float) -> tuple[tuple[float, float, float, float, str], ...]:
    """The rectangles, shrunk towards the centre of the grid by ``inset``."""
    factor = 1.0 - inset
    middle = GRID / 2

    def s(value: float) -> float:
        return middle + (value - middle) * factor

    return tuple((s(x0), s(y0), s(x1), s(y1), c) for x0, y0, x1, y1, c in RECTS)


def svg(inset: float = 0.0) -> str:
    """One icon as a standalone document, from the same rectangles the PNGs are built from."""
    body = "".join(
        f'<rect x="{x0:g}" y="{y0:g}" width="{x1 - x0:g}" height="{y1 - y0:g}" fill="{c}"/>'
        for x0, y0, x1, y1, c in scaled(inset)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-label="Systems From Scratch">'
        f'<rect width="64" height="64" fill="{BACKGROUND}"/>{body}</svg>\n'
    )


def _rgb(colour: str) -> tuple[int, int, int]:
    return tuple(int(colour[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def raster(size: int, inset: float = 0.0) -> list[bytearray]:
    """The icon as rows of RGB bytes, by exact area coverage rather than by rendering.

    A pixel's coverage by an axis-aligned rectangle is the overlap in x times the overlap in y,
    so an edge that falls between two pixels is antialiased correctly and one that falls on a
    boundary is exact. No sampling, and the same answer everywhere.
    """
    per_unit = size / GRID
    rows = [bytearray(_rgb(BACKGROUND) * size) for _ in range(size)]

    for x0, y0, x1, y1, colour in scaled(inset):
        left, right = x0 * per_unit, x1 * per_unit
        top, bottom = y0 * per_unit, y1 * per_unit
        red, green, blue = _rgb(colour)
        for py in range(max(0, int(top)), min(size, int(bottom) + 1)):
            up = min(py + 1.0, bottom) - max(float(py), top)
            if up <= 0:
                continue
            row = rows[py]
            for px in range(max(0, int(left)), min(size, int(right) + 1)):
                across = min(px + 1.0, right) - max(float(px), left)
                if across <= 0:
                    continue
                alpha = across * up
                at = px * 3
                if alpha >= 1.0:
                    row[at : at + 3] = bytes((red, green, blue))
                else:
                    rest = 1.0 - alpha
                    row[at] = round(row[at] * rest + red * alpha)
                    row[at + 1] = round(row[at + 1] * rest + green * alpha)
                    row[at + 2] = round(row[at + 2] * rest + blue * alpha)
    return rows


# -- the containers ---------------------------------------------------------------------------


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def png(rows: list[bytearray]) -> bytes:
    """Encode as 8-bit RGB with no filtering.

    Filter 0 on every row costs a few hundred bytes at these sizes and makes ``--check`` cheap:
    decoding is slicing, with none of the per-byte prediction the other filters need.
    """
    height, width = len(rows), len(rows[0]) // 3
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def png_rows(data: bytes) -> list[bytearray]:
    """Decode what ``png`` wrote, and refuse anything else."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    position, idat, header = 8, b"", None
    while position < len(data):
        (length,) = struct.unpack(">I", data[position : position + 4])
        kind = data[position + 4 : position + 8]
        body = data[position + 8 : position + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        position += 12 + length
    if header is None:
        raise ValueError("no IHDR")
    width, height, depth, colour = header[0], header[1], header[2], header[3]
    if (depth, colour) != (8, 2):
        raise ValueError("not 8-bit RGB")
    raw, stride, out = zlib.decompress(idat), width * 3, []
    for index in range(height):
        start = index * (stride + 1)
        if raw[start] != 0:
            raise ValueError("filtered rows are not written by this script")
        out.append(bytearray(raw[start + 1 : start + 1 + stride]))
    return out


def ico(images: dict[int, bytes]) -> bytes:
    """Wrap PNGs in an ICO container, which every browser in use understands."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    directory, payload = b"", b""
    for size, image in sorted(images.items()):
        edge = size if size < 256 else 0
        directory += struct.pack("<BBBBHHII", edge, edge, 0, 0, 1, 24, len(image), offset)
        payload += image
        offset += len(image)
    return header + directory + payload


def manifest() -> str:
    """The web app manifest, with every path relative to the manifest itself.

    This is a project site served under a prefix, so an absolute path would have to know it.
    Resolved against the manifest's own URL these are right wherever the site is mounted, which
    is why ``start_url`` is "." as well.
    """
    icons = ",\n".join(
        f'    {{ "src": "{src}", "sizes": "{size}x{size}", '
        f'"type": "image/png", "purpose": "{purpose}" }}'
        for src, size, purpose in (
            ("icon-192.png", 192, "any"),
            ("icon-512.png", 512, "any"),
            ("icon-maskable-512.png", 512, "maskable"),
        )
    )
    return (
        "{\n"
        '  "name": "Systems From Scratch",\n'
        '  "short_name": "Systems",\n'
        '  "start_url": ".",\n'
        '  "display": "minimal-ui",\n'
        f'  "background_color": "{BACKGROUND}",\n'
        f'  "theme_color": "{BACKGROUND}",\n'
        '  "icons": [\n'
        f"{icons}\n"
        "  ]\n"
        "}\n"
    )


# -- the two entry points ---------------------------------------------------------------------


def write() -> int:
    ICONS.mkdir(exist_ok=True)
    written = []

    for name, inset in (("icon.svg", 0.0), ("icon-maskable.svg", 0.18)):
        (ICONS / name).write_text(svg(inset))
        written.append(name)

    (ICONS / "site.webmanifest").write_text(manifest())
    written.append("site.webmanifest")

    for name, (size, inset) in RASTERS.items():
        (ICONS / name).write_bytes(png(raster(size, inset)))
        written.append(name)

    (ICONS / "favicon.ico").write_bytes(ico({size: png(raster(size)) for size in ICO_SIZES}))
    written.append("favicon.ico")

    for name in written:
        print(f"  icons/{name}")
    return 0


def check() -> int:
    problems: list[str] = []

    expected_text = {
        "icon.svg": svg(),
        "icon-maskable.svg": svg(0.18),
        "site.webmanifest": manifest(),
    }
    for name, body in expected_text.items():
        path = ICONS / name
        if not path.is_file():
            problems.append(f"{name} is missing")
        elif path.read_text() != body:
            problems.append(f"{name} is not what the code writes")

    for name, (size, inset) in RASTERS.items():
        path = ICONS / name
        if not path.is_file():
            problems.append(f"{name} is missing")
            continue
        try:
            found = png_rows(path.read_bytes())
        except (ValueError, zlib.error) as error:
            problems.append(f"{name} could not be read: {error}")
            continue
        if len(found) != size or len(found[0]) != size * 3:
            problems.append(f"{name} is not {size}x{size}")
        elif found != raster(size, inset):
            problems.append(f"{name} does not match what the code draws")

    path = ICONS / "favicon.ico"
    if not path.is_file():
        problems.append("favicon.ico is missing")
    elif path.read_bytes() != ico({size: png(raster(size)) for size in ICO_SIZES}):
        problems.append("favicon.ico is not what the code writes")

    if problems:
        print("make-icons: FAILED", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("  run: python3 scripts/make-icons.py", file=sys.stderr)
        return 1

    print(f"make-icons: OK ({len(expected_text) + len(RASTERS) + 1} file(s), pixel for pixel)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify, do not write")
    args = parser.parse_args()
    return check() if args.check else write()


if __name__ == "__main__":
    raise SystemExit(main())
