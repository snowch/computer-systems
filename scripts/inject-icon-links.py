#!/usr/bin/env python3
"""Put the home-screen icon links into every built page's ``<head>``.

The book theme emits one icon link, ``<link rel="icon" href="…/favicon.ico">``, and has no
option for anything else — its published option list (``analytics_google``, ``favicon``,
``logo``, ``style`` and the rest) contains no way to add to the head. So the tags that decide
what a phone shows when somebody saves the page are added here, after the build.

**What each tag is for, and why the favicon is not enough.**

- ``apple-touch-icon`` is the only thing iOS Safari will use for a home-screen tile. Without it
  Safari saves a shrunken screenshot of the page, which is what this book had.
- ``manifest`` gives Android Chrome a name, a colour and a set of icons, including the maskable
  one it crops to whatever shape the launcher uses.
- ``icon`` with ``type="image/svg+xml"`` is what a browser prefers for a tab when it has one,
  and it stays sharp at any size.
- ``theme-color`` colours the address bar, and the splash screen a saved page opens with.

Safari does look for ``/apple-touch-icon.png`` on its own when no link says otherwise, but it
looks at the *domain* root. This is a project site served from a subdirectory, so that fallback
lands on somebody else's page and the link tag is the only way.

Usage::

    python3 scripts/inject-icon-links.py _build/html /computer-systems
    python3 scripts/inject-icon-links.py _build/html /computer-systems --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

#: The tags to add, in the order a reader of the HTML would want to find them. Each is a
#: ``{base}``-relative path so one build can serve from a subdirectory and another from a root.
TAGS = (
    '<link rel="apple-touch-icon" sizes="180x180" href="{base}/apple-touch-icon.png"/>',
    '<link rel="icon" type="image/svg+xml" href="{base}/icon.svg"/>',
    '<link rel="manifest" href="{base}/site.webmanifest"/>',
    '<meta name="theme-color" content="#1a1a1a"/>',
)

#: Every file the tags above point at, plus the ones the manifest names. `myst.yml` has to ship
#: all of these as `static_files`, and a test compares the two lists so a tag cannot come to
#: reference a file nobody copies.
REFERENCED = (
    "apple-touch-icon.png",
    "icon.svg",
    "site.webmanifest",
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-512.png",
)

#: How the injection recognises its own work, so running twice changes nothing.
MARKER = 'rel="apple-touch-icon"'


def head_block(base: str) -> str:
    return "".join(tag.format(base=base.rstrip("/")) for tag in TAGS)


def pages(root: Path) -> list[Path]:
    return sorted(root.rglob("*.html"))


def inject(root: Path, base: str, *, dry_run: bool = False) -> tuple[int, int, list[str]]:
    """Add the tags to every page that lacks them. Returns (changed, skipped, problems)."""
    block, changed, skipped, problems = head_block(base), 0, 0, []
    found = pages(root)
    if not found:
        return 0, 0, [f"no HTML under {root} — did the build run?"]

    for page in found:
        text = page.read_text(encoding="utf-8")
        if MARKER in text:
            skipped += 1
            continue
        if "</head>" not in text:
            problems.append(f"{page.relative_to(root)} has no </head>")
            continue
        if not dry_run:
            page.write_text(text.replace("</head>", f"{block}</head>", 1), encoding="utf-8")
        changed += 1

    return changed, skipped, problems


def check_assets(html: Path) -> list[str]:
    """Confirm the build really did publish the files the tags point at.

    This runs on every deploy because it is the only place the two config mechanisms can be
    checked at all. `static_files` and the theme's `favicon` option are both real — one is in
    mystmd's own config validator, the other in the book theme's published option list — but a
    themed build needs the template registry, which is not reachable from every environment, so
    the author cannot always watch it work before pushing. If either silently stops placing
    files, this turns a wrong icon into a failed deploy.
    """
    problems = []
    for name in REFERENCED:
        if not (html / name).is_file():
            problems.append(
                f"{name} was not published. myst.yml ships it as `static_files`; if that list "
                "is right, the mechanism has changed."
            )

    # The theme emits <link rel="icon" href="…/favicon.ico"> whether or not anybody set one, and
    # serves its own logo when nobody has. A missing favicon is therefore invisible: the tab just
    # shows somebody else's mark.
    built, source = (
        html / "favicon.ico",
        Path(__file__).resolve().parent.parent / "icons" / "favicon.ico",
    )
    if not built.is_file():
        problems.append("favicon.ico was not published — check `site.options.favicon` in myst.yml")
    elif source.is_file() and built.read_bytes() != source.read_bytes():
        problems.append(
            "the published favicon.ico is not icons/favicon.ico, so the tab is showing something "
            "else. If the theme has started re-encoding it, ship it through `static_files` "
            "instead and drop `site.options.favicon`."
        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="the built site, usually _build/html")
    parser.add_argument("base", nargs="?", default="", help="BASE_URL the site is served under")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change and fail if anything would, without writing",
    )
    args = parser.parse_args()

    missing = check_assets(args.html)
    if missing:
        print("inject-icon-links: FAILED", file=sys.stderr)
        for problem in missing:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    changed, skipped, problems = inject(args.html, args.base, dry_run=args.check)

    for problem in problems:
        print(f"inject-icon-links: {problem}", file=sys.stderr)
    if problems:
        return 1

    if args.check and changed:
        print(f"inject-icon-links: {changed} page(s) still need the tags", file=sys.stderr)
        return 1

    print(f"inject-icon-links: {changed} page(s) given icon links, {skipped} already had them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
