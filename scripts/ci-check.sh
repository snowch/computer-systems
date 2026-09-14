#!/usr/bin/env bash
# Exactly what CI runs. Run it before pushing.
#
# CI invokes this same script, so the two cannot drift (PLAN.md §9). Nothing here needs the
# reference machine: board-only tests skip themselves, and every host-target example is
# cross-compiled and executed under user-mode QEMU, which checks that it is correct and says
# nothing about what it costs.
set -euo pipefail

cd "$(dirname "$0")/.."

PY_PATHS=(bench scripts tests)

echo "== ruff lint =="
ruff check "${PY_PATHS[@]}"

echo "== ruff format =="
ruff format --check "${PY_PATHS[@]}"

echo "== pytest =="
# `python3 -m pytest`, not bare `pytest`: the module form runs the tests under the interpreter
# that has the project's dependencies. A standalone pytest (pipx, uv tool) has its own isolated
# environment and cannot import bench.
#
# -m "not problem" deselects the chapter problems. They are the reader's work and they fail
# until solved, which is the whole design — a suite that went red for an unsolved exercise would
# train everyone to ignore it. What CI does check is that each problem is *answerable*: the
# scaffolding tests beside them compile the C, stage it into the kernel and boot it.
python3 -m pytest tests/ -q -m "not problem"

echo "== benchmark result stamps =="
python3 scripts/verify-numbers.py

echo "== disassembly listings still match the compiler =="
# The one artefact in the book that CI can regenerate rather than trust. A listing depends on the
# compiler, not on the machine, so re-capturing it here asks a question no other check can: does
# the toolchain a reader is told to install still emit the instructions the chapters discuss?
#
# A failure is not noise. Either the source moved without the listing being re-rendered, or the
# compiler changed its mind — and a chapter explaining a `csel` that gcc no longer emits is
# simply wrong. Both are fixed by `make bench-listings && make figures`.
python3 -m bench.run_disasm --check

echo "== figures and tables up to date =="
python3 scripts/render-figures.py --check

echo "== myst content build (strict) =="
if ! command -v myst >/dev/null 2>&1; then
  if [ -n "${CI:-}" ]; then
    # A check that silently skips itself is not a check. CI installs myst, so its absence here
    # means the workflow is misconfigured; fail loudly rather than publish a broken link.
    echo "ERROR: myst is not installed and CI must not skip the book build." >&2
    exit 1
  fi
  echo "  myst not installed; skipping locally."
  echo "  install with: npm install -g \"mystmd@$(node -p "require('./package.json').devDependencies.mystmd")\""
  echo
  echo "All checks passed."
  exit 0
fi

# Content build WITHOUT --html. This matters: with --html, MyST downloads the site theme before
# it parses anything, so where the template registry is unreachable the build aborts having
# validated nothing at all. Without it, every page is parsed first and only the final site
# assembly fails — so the log still says whether the content is sound.
log=$(mktemp)
myst build --strict > "$log" 2>&1 || true

# Two conditions, both required. The page count proves parsing actually happened, so a build that
# died early can never be mistaken for a clean one; the warning check is the verdict.
if ! grep -qE "Built [0-9]+ pages" "$log"; then
  echo "ERROR: myst did not parse any pages — the build failed before validating content." >&2
  tail -25 "$log" >&2
  rm -f "$log"
  exit 1
fi
if grep -qE "⚠|⛔" "$log"; then
  echo "ERROR: content warnings (broken reference, citation or literalinclude anchor):" >&2
  grep -E "⚠|⛔" "$log" >&2
  rm -f "$log"
  exit 1
fi
echo "  $(grep -oE 'Built [0-9]+ pages' "$log" | tail -1), no warnings"
rm -f "$log"

echo "== the PDF renderer sees every page =="
# The mdast-to-HTML renderer is the one part of the pipeline that is not MyST's, and it raises on
# a node type it does not handle rather than dropping content. Running it over every page on
# every push is what stops a new directive from silently disappearing out of the PDF. No Chromium
# here on purpose: assembling the HTML is what touches every page, and printing it is the cheap
# part CI does not need to repeat.
python3 scripts/build-pdf.py --no-myst --html-only --out _build/pdf-check/book.pdf > /dev/null
echo "  every page rendered"

echo "== myst themed HTML build =="
# Needs the MyST template registry and GitHub. Mandatory in CI; locally a blocked host says
# nothing about the book, since the content build above already validated everything authored.
if [ -n "${CI:-}" ]; then
  myst build --html --strict
  echo "  themed build OK"
elif myst build --html --strict > /dev/null 2>&1; then
  echo "  themed build OK"
else
  echo "  SKIPPED: cannot reach the MyST template registry from this environment."
fi

echo
echo "All checks passed."
