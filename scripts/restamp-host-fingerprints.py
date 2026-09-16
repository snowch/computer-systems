#!/usr/bin/env python3
"""Re-stamp the ``code_fingerprint`` of ``host/measurement`` results after a comment-only edit.

A result names its sources and hashes their raw bytes, so editing a *comment* in one of those
sources — renaming ``chNN`` to the chapter it means — changes the fingerprint even though the
number the result records cannot have moved: a comment does not compile to anything and cannot
change a duration. For every other kind of result the fix is to re-run the runner (the listings and
the structural xv6/bare results regenerate under QEMU, and the regen workflow does exactly that).
A ``host/measurement`` is the one kind that cannot be re-run off the board, and re-running it would
throw away a real timing to replace it with another real timing that says the same thing.

So this script recomputes the fingerprint from the sources as they now stand and writes it back,
for ``host/measurement`` results only, and prints every change. It refuses to touch a result of any
other target or kind: those must go through their runner, which also re-captures the output and so
proves the edit really was comment-only. The same proof is available here indirectly — a
``host/measurement`` source almost always also feeds a ``host/listing``, and the regen workflow
re-captures that disassembly; if a supposedly-cosmetic edit changed an instruction, that listing
moves and CI fails. This script is the board timings riding along with an edit whose only effect on
them is to the hash of the bytes they were built from.

Usage: ``python3 scripts/restamp-host-fingerprints.py [--check]``. With ``--check`` it reports what
would change and exits non-zero if anything would, writing nothing — for CI or a dry run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench.stamp import ROOT, code_fingerprint  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change and exit non-zero if anything would; write nothing",
    )
    args = parser.parse_args()

    changed: list[str] = []
    for path in sorted((ROOT / "bench" / "results").glob("*.json")):
        payload = json.loads(path.read_text())
        if payload.get("target") != "host" or payload.get("kind") != "measurement":
            continue
        recorded = payload.get("code_fingerprint")
        expected = code_fingerprint(payload.get("code_sources"), payload.get("target"))
        if recorded == expected:
            continue
        changed.append(f"{path.name}: {recorded} -> {expected}")
        if not args.check:
            payload["code_fingerprint"] = expected
            # Byte-for-byte the format bench.stamp writes, so the diff is one line per file.
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    if not changed:
        print("Every host/measurement fingerprint already matches its sources.")
        return 0

    verb = "would change" if args.check else "re-stamped"
    print(f"{verb} {len(changed)} host/measurement fingerprint(s):")
    for line in changed:
        print(f"  {line}")
    return 1 if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
