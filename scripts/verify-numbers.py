#!/usr/bin/env python3
"""Refuse to publish a number the book cannot defend.

Six rules. Each one exists because the failure it catches is silent — a wrong number looks
exactly like a right one, and the reader has no way to tell.

1. **Every figure's result exists.** A chapter that cites a run nobody made fails here rather
   than rendering an empty table.
2. **Every result carries its stamps** — target, machine, kernel, compiler, flags. A measurement
   whose conditions are unknown cannot be checked by anyone, including its author in six months.
3. **Every result was produced by the code that is checked in.** A content hash over the shared
   core plus the runner's own sources, so editing the code invalidates the number instead of
   quietly contradicting it. Comparing commit *times* instead cannot tell an unrelated new file
   from a change to the thing being measured, and is wrong in both directions.
4. **Provenance matches the target and the kind.** A ``host`` number must have been measured
   natively on the reference machine, and an ``xv6`` result must not contain a timing at all. This
   is the rule that protects the book's central claim: QEMU will answer a question about
   nanoseconds, and the answer is fiction, so the repository does not allow one to be recorded.
   Disassembly listings are exempt from the first half — instructions do not depend on which
   computer ran the compiler — and are held to their own rules instead, which is what stops the
   exemption from becoming a way round the board.
5. **A pending figure whose result has landed is an error.** Otherwise a measurement gets taken
   and the book goes on saying it is missing.
6. **No measured figure is typed into chapter prose**, where regenerating results would silently
   leave it behind.

Fragment freshness is a separate check: ``scripts/render-figures.py --check``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.figures import cited_results, pending_results  # noqa: E402
from bench.stamp import (  # noqa: E402
    REQUIRED_STAMPS,
    RESULTS_DIR,
    code_fingerprint,
    provenance_problems,
)

CHAPTERS = ROOT / "chapters"
APPENDICES = ROOT / "appendices"

#: Units that make a claim about cost. A figure carrying one of these belongs in a generated
#: fragment, because it can only have come from a run that might be redone.
#:
#: Frequencies are deliberately absent. "1.5 GHz" is a specification, not a measurement, and
#: §5 allows a specification when it cites a primary source.
COST_UNITS = r"ns|µs|us|ms|s|cycles?|instructions|IPC|[KMG]i?B/s|bytes/cycle"
MEASURED_FIGURE = re.compile(
    rf"\b\d+(?:[.,]\d+)?\s*(?:{COST_UNITS})\b" rf"|\b\d+\.\d+\s*[x×]\b" rf"|\b\d+(?:\.\d+)?\s*%"
)

#: A MyST comment on the line before, for a figure that is legitimately a cited specification
#: rather than a measurement. It leaves the reason in the source where a reviewer will see it.
EXEMPTION = re.compile(r"^%\s*number-ok:\s*\S+")


def check_results(problems: list[str]) -> int:
    """Rules 1–5."""
    pending = pending_results()

    for name in sorted(cited_results()):
        if not (RESULTS_DIR / f"{name}.json").exists():
            problems.append(
                f"missing result: bench/results/{name}.json is cited by a figure. "
                f"Generate it with the runner named by `grep -rl {name} bench/run_*.py`."
            )

    for name, reason in sorted(pending.items()):
        if (RESULTS_DIR / f"{name}.json").exists():
            problems.append(
                f"bench/results/{name}.json exists but its figure is still marked pending "
                f"({reason!r}). Remove the `pending=` argument in bench/figures.py and "
                "re-render — the measurement has landed."
            )

    checked = 0
    for path in sorted(RESULTS_DIR.glob("*.json")):
        name = path.stem
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{name}.json is not valid JSON: {exc}")
            continue
        checked += 1

        for stamp in REQUIRED_STAMPS:
            if stamp not in payload:
                problems.append(f"{name}.json is missing the required '{stamp}' stamp")
        if not all(stamp in payload for stamp in ("target", "machine", "summary")):
            continue

        recorded = payload.get("code_fingerprint")
        if recorded is None:
            problems.append(f"{name}.json has no code_fingerprint — regenerate it")
        else:
            try:
                expected = code_fingerprint(payload.get("code_sources"))
            except FileNotFoundError as exc:
                problems.append(f"{name}.json names a source that no longer exists: {exc}")
                expected = None
            if expected is not None and recorded != expected:
                problems.append(
                    f"{name}.json was produced by different code than is checked in "
                    f"(stamped {recorded}, now {expected}) — re-run the runner that writes it, "
                    "or delete the file if nothing produces it any more"
                )

        problems += provenance_problems(f"{name}.json", payload)

    return checked


def check_prose(problems: list[str]) -> None:
    """Rule 6: a measured figure typed into a sentence is one nobody will ever regenerate."""
    for directory in (CHAPTERS, APPENDICES):
        for source in sorted(directory.glob("*.md")):
            lines = source.read_text().splitlines()
            fenced = False
            for n, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("```"):
                    fenced = not fenced
                    continue
                # Generated tables, their caption lines, and directive options carry real
                # figures legitimately.
                if fenced or stripped.startswith(("|", ":", "*Conditions", "%", "<!--")):
                    continue
                if n >= 2 and EXEMPTION.match(lines[n - 2].strip()):
                    continue
                for hit in MEASURED_FIGURE.findall(line):
                    problems.append(
                        f"{source.relative_to(ROOT)}:{n} types the measured figure "
                        f"'{hit.strip()}' into prose. Put it in a generated fragment "
                        "(AUTHORING_GUIDE.md), or, if it is a cited specification rather than a "
                        "measurement, precede the line with `% number-ok: <citation>`."
                    )


def main() -> int:
    problems: list[str] = []
    checked = check_results(problems)
    check_prose(problems)

    if problems:
        print("verify-numbers: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    pending = pending_results()
    note = f", {len(pending)} figure(s) awaiting the board" if pending else ""
    print(f"verify-numbers: OK ({checked} result file(s) stamped and verified{note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
