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

echo "== every displayed chapter number still matches the outline =="
# A chapter number is a number, so it is derived rather than typed. The anchors are slugs
# and never move; what this catches is a link whose *text* still says ch17 after the
# chapter became ch18 — which --strict cannot see, because the anchor still resolves.
python3 scripts/sync-labels.py --check

echo "== benchmark result stamps =="
python3 scripts/verify-numbers.py

echo "== a fresh xv6 boot still gives the answers the book publishes =="
# The complement to verify-numbers.py, and the one check it cannot perform. That script hashes
# the *files* a result names, and the xv6 submodule commit is not a file — neither is the set of
# patches under xv6/patches/, as far as a fingerprint over source is concerned. So bumping the
# submodule or adding a kernel patch can change what the kernel reports while every fingerprint
# still matches, and the book goes on publishing a number nothing produces any more.
#
# the traps-and-system-calls chapter did exactly that: its census patch grew the kernel and its workload added a user program,
# and the committed setup result described the kernel of five chapters earlier. This check lived
# only in .github/workflows/quality.yml at the time, so six commits passed `make check` locally
# while CI was red. That is the whole argument for this script being the single source of truth:
# a check CI runs and a contributor cannot is a check that fails after the push.
python3 -m bench.run_setup --target xv6 --check

echo "== disassembly listings still match the compiler =="
# The one artefact in the book that CI can regenerate rather than trust. A listing depends on the
# compiler, not on the machine, so re-capturing it here asks a question no other check can: does
# the toolchain a reader is told to install still emit the instructions the chapters discuss?
#
# A failure is not noise. Either the source moved without the listing being re-rendered, or the
# compiler changed its mind — and a chapter explaining a `csel` that gcc no longer emits is
# simply wrong. Both are fixed by `make bench-listings && make figures`.
python3 -m bench.run_disasm --check

echo "== the toolchain still produces the files the program-end-to-end chapter counts =="
# Same argument as the listings above: sizes and symbol counts are compiler output, not machine
# measurements, so CI can re-derive them rather than trust the committed copy. This one also
# builds xv6, because one of the numbers is the size of the same program linked by xv6's own
# user library — the comparison the program-end-to-end chapter closes on.
python3 -m bench.run_stages --check
python3 -m bench.run_frames --check
python3 -m bench.run_elf --check

echo "== the trap census still says what the book prints =="
# Boots the patched kernel and re-runs the traps-and-system-calls chapter's workload. Only the deterministic half of the census
# is recorded, so this is a real check rather than a coin toss: a patch that changed how many
# system calls the shell makes would move the number, and moving it silently is the failure the
# whole stamping scheme exists to prevent.
python3 -m bench.run_traps --check

echo "== the page tables still have the shape the book prints =="
# Boots the kernel and dumps its own map and init's. Both are decided by the build rather than by
# the run, so this is a real check: a kernel patch that changed the layout, or a submodule bump
# that moved a mapping, would show up here as a shape the chapter no longer describes.
#
# It also re-runs the virtual-memory chapter's cross-check — the Sv39 model derives the table count from the addresses,
# the kernel counts by walking — and refuses to stamp or pass if the two stop agreeing.
python3 -m bench.run_pagetable --check

echo "== the fault census still costs what the book prints =="
# the page-faults chapter's exchange rate: pages allocated and faults taken, under each of the kernel's two
# allocation policies. The workload fixes every quantity and prints them, and the runner refuses
# a census that disagrees with the program, one latched from a different process, or one in which
# the handler declined a fault.
python3 -m bench.run_faults --check

echo "== the interrupt census still says what the book prints =="
# the interrupts-and-drivers chapter's disk figure depends on the filesystem image as well as on the code, and nothing else in
# the stamping scheme covers fs.img — so this check is the only thing that would notice a later
# chapter adding an xv6 program and moving the number. The console counts this deliberately does
# not record are the ones that vary; see the runner's docstring.
python3 -m bench.run_interrupts --check

echo "== the lock is still made of the instructions the book prints =="
# Read out of the kernel as built, so this catches a compiler that stopped emitting the atomic or
# the fence — either of which would be a broken lock, and neither of which any test would notice.
python3 -m bench.run_locks --check

echo "== a context switch still moves what the book says =="
python3 -m bench.run_switch --check

echo "== one byte still costs the disk what the book prints =="
python3 -m bench.run_blocks --check

echo "== both targets still agree about the two-routes chapter's program =="
python3 -m bench.run_bridge --check

echo "== the compiler still makes the same of the optimisation chapter's five loops =="
python3 -m bench.run_loops --check

echo "== the compiler still leaves the pipeline chapter a branch to measure =="
python3 -m bench.run_pipeline --check

echo "== the false-sharing chapter's counters still land where the book says =="
python3 -m bench.run_sharing --check

echo "== the profiling chapter's program still has the shape it profiles =="
python3 -m bench.run_profile --check

echo "== the memory-as-one-array chapter's first program still says what it quotes =="
python3 -m bench.run_firstc --check

echo "== the kernel still lacks what the freestanding-C chapter says it lacks =="
python3 -m bench.run_kernelc --check

echo "== Part II's programs still do what their chapters say =="
# These boot for real, on a machine with no operating system on it, and each one is refused
# unless it still demonstrates its chapter's claim. A program that merely boots and exits proves
# nothing: the bare-metal trap chapter's trap could resume without having been taken, the bare-metal paging chapter's harts could lose nothing.
python3 -m bench.run_bare --check

echo "== appendix D still describes the kernel tree that is checked out =="
python3 -m bench.run_filemap --check

echo "== the compiler still refuses the vectors chapter's three loops =="
python3 -m bench.run_vectors --check

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
