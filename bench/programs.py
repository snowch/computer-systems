"""Every program in this book that a reader can run, and how to run it.

The book's first invariant is that no code is pasted into prose: every listing is a
`{literalinclude}` of a file that really compiles. That makes the snippets honest, and it does
nothing at all for a reader who wants to change one and see what happens — which is most of the
point. Working out how to build `sysfs/bare/trap.c` means reconstructing `-fno-pic`,
`-mcmodel=medany`, a linker script and `-bios none` from a Python module they have no reason to
have opened.

So this is the registry the `./run` script uses, and it is **derived rather than listed**. A
program is a `.c` file in one of four directories; its target is the directory it is in; its
description is the first line of its own opening comment, which every one of them already has.
Nothing here needs updating when a program is added, which is the only kind of index that stays
true.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bench.stamp import ROOT

#: Linked into every bare-metal program rather than being programs themselves.
BARE_RUNTIME = {"start.S", "console.c", "syscalls.c"}

#: Where each target's programs live.
SOURCE_DIRS = {
    "bare": ROOT / "sysfs" / "bare",
    "host": ROOT / "sysfs" / "tools",
    "hostbench": ROOT / "sysfs" / "bench",
    "xv6": ROOT / "xv6" / "apps",
}

#: The first line of a program's opening comment, which every one of them has. The forms vary --
#: `/* firstc — one complete C program`, `/* ch06 (first half): one page table`,
#: `/* trapload, xv6 target: ask the kernel` -- so the rule is "whatever follows the first dash or
#: colon", and a line with neither is taken whole.
OPENING = re.compile(r"^/\*\s*(.+?)\s*$", re.MULTILINE)
SEPARATOR = re.compile(r"\s*(?:—|:|\s-\s)\s*")

#: Programs needing more than one hart. Everything else gets one, which is the honest default:
#: a program that does not say it wants two harts should not silently be given them.
HARTS = {"harts": 2}


@dataclass(frozen=True)
class Program:
    name: str
    #: `bare`, `host` or `xv6` — what the reader needs installed, and how it is started.
    target: str
    source: Path
    what: str

    @property
    def relative(self) -> str:
        return str(self.source.relative_to(ROOT))

    @property
    def harts(self) -> int:
        return HARTS.get(self.name, 1)

    @property
    def command(self) -> str:
        """What a chapter tells the reader to type. One source of truth for the prose too."""
        return f"./run {self.name}"


def _describe(source: Path) -> str:
    match = OPENING.search(source.read_text())
    if not match:
        return ""
    line = match.group(1)
    parts = SEPARATOR.split(line, maxsplit=1)
    # The opening line is a sentence about the program; drop the full stop so it reads as a label.
    return (parts[1] if len(parts) > 1 else line).rstrip(".")


def _libraries(source: Path) -> list[Path]:
    """The library sources a host program needs, worked out from what it includes.

    `#include "sysfs/timing.h"` means `sysfs/lib/timing.c` has to be linked. Reading that off the
    includes rather than keeping a table means a program that starts using the clock does not also
    have to be remembered here.
    """
    text = source.read_text()
    found = []
    for header in re.findall(r'#include\s+"sysfs/([\w]+)\.h"', text):
        library = ROOT / "sysfs" / "lib" / f"{header}.c"
        if library.exists():
            found.append(library)
    return found


def discover() -> tuple[Program, ...]:
    programs: list[Program] = []
    for target, directory in SOURCE_DIRS.items():
        if not directory.is_dir():
            continue
        for source in sorted(directory.glob("*.c")):
            if source.name in BARE_RUNTIME:
                continue
            programs.append(
                Program(
                    name=source.stem,
                    target="host" if target == "hostbench" else target,
                    source=source,
                    what=_describe(source),
                )
            )
    return tuple(programs)


PROGRAMS: tuple[Program, ...] = discover()


#: Two targets can hold a program of the same name — `sameanswer` and `sysprobe` exist for both
#: `host` and `xv6`, which is the point of ch21. Looking one up by name alone is therefore
#: ambiguous, and the lookup says so rather than picking.
def find(name: str, target: str | None = None) -> Program:
    matches = [p for p in PROGRAMS if p.name == name and (target is None or p.target == target)]
    if not matches:
        known = ", ".join(sorted({p.name for p in PROGRAMS}))
        raise KeyError(f"no program called {name!r}. There is: {known}")
    if len(matches) > 1:
        targets = ", ".join(sorted(p.target for p in matches))
        raise KeyError(
            f"{name!r} exists for more than one target ({targets}) — say which, e.g. "
            f"`./run {name} --target {matches[0].target}`"
        )
    return matches[0]


def libraries_for(program: Program) -> list[Path]:
    return _libraries(program.source)
