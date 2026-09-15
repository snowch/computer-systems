#!/usr/bin/env python3
"""Every local file a built page links to is a file that was actually built.

    python3 scripts/check-built-links.py _build/html

The preface offers the whole book as a PDF. It has been offering a 404: `BASE_URL` is
`/computer-systems` with no trailing slash, the link was written `systems-from-scratch.pdf`
relative, and the theme concatenated the two into `/computer-systemssystems-from-scratch.pdf`.

Nothing could have caught that. `myst build --strict` checks cross-references between *pages* and
is right not to care about a static asset; the PDF itself built and uploaded perfectly well; and
the link is in the one file nobody re-reads after the first week. It was only ever going to be
found by a reader clicking it, which is what happened.

So this runs against the built site, after everything is in place, and resolves each link the way
a browser would. A link to a file that is not there fails the deploy rather than shipping.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: Links to a file rather than to a page. A page is the theme's business and `--strict` has
#: already checked those; these are the ones that silently 404.
FILE_LINK = re.compile(r'href="([^"#?]+\.(?:pdf|zip|tar\.gz|json|csv|txt|svg|png))"')

#: Where the site is served from, e.g. `/computer-systems`. Stripped before resolving a link
#: against the build directory, because on disk the build directory *is* that prefix.
BASE = sys.argv[2] if len(sys.argv) > 2 else ""


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "_build/html")
    if not root.is_dir():
        print(f"check-built-links: {root} is not a directory", file=sys.stderr)
        return 2

    broken: list[str] = []
    checked = 0
    for page in sorted(root.rglob("*.html")):
        for href in FILE_LINK.findall(page.read_text(errors="ignore")):
            if href.startswith(("http://", "https://", "//", "data:", "mailto:")):
                continue
            checked += 1
            if href.startswith("/"):
                # As a path segment, not as a string prefix. Stripping it as a prefix is how the
                # first version of this check passed the very link it was written to catch:
                # "/computer-systemssystems-from-scratch.pdf" starts with "/computer-systems",
                # and what was left resolved to a file that does exist.
                if BASE and (href == BASE or href.startswith(BASE + "/")):
                    path = href[len(BASE) :]
                else:
                    path = href
                target = root / path.lstrip("/")
            else:
                target = (page.parent / href).resolve()
            if not target.exists():
                broken.append(f"{page.relative_to(root)} links to {href!r}, which is not there")

    if broken:
        print(f"check-built-links: FAILED ({len(broken)} of {checked})")
        for line in sorted(set(broken)):
            print(f"  - {line}")
        return 1
    print(f"check-built-links: OK ({checked} file link(s), all resolve)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
