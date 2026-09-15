# Systems From Scratch — the commands the book tells you to run.
#
# Two execution targets, and the split runs through everything here:
#
#   xv6   — the teaching kernel under qemu-system-riscv64. Structure and semantics. Runs
#           anywhere, including CI, and never produces a timing.
#   host  — Linux on real hardware, natively over SSH. Every number about cost.
#
# `make bench-board` is the only target that must run on the board, and it refuses to run
# anywhere else rather than quietly producing an emulated number (ch00).

PYTHON ?= python3
SHELL  := /bin/bash

.DEFAULT_GOAL := help

.PHONY: help
help:  ## Show this list
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# -- setup -------------------------------------------------------------------------------

.PHONY: verify
verify:  ## Check this machine and report which targets it can run (ch00)
	$(PYTHON) scripts/verify-setup.py

.PHONY: submodule
submodule:  ## Fetch the xv6 submodule
	git submodule update --init --recursive

# -- the xv6 target ----------------------------------------------------------------------

.PHONY: xv6-build
xv6-build:  ## Stage xv6 with the book's apps and patches, and compile it
	$(PYTHON) scripts/xv6-run.py --build-only

.PHONY: xv6-qemu
xv6-qemu:  ## Boot xv6 under QEMU and hand over the terminal (Ctrl-A X to quit)
	$(PYTHON) scripts/xv6-run.py

.PHONY: xv6-gdb
xv6-gdb:  ## Boot xv6 halted at reset, waiting for gdb on :26000 (Appendix B)
	$(PYTHON) scripts/xv6-run.py --gdb

.PHONY: xv6-clean
xv6-clean:  ## Delete the staging tree; the submodule is never touched
	rm -rf xv6/stage

# -- measurements ------------------------------------------------------------------------

.PHONY: bench-xv6
bench-xv6:  ## Re-run every xv6-target measurement (runs anywhere QEMU does)
	$(PYTHON) -m bench.run_setup --target xv6

.PHONY: bench-listings
bench-listings:  ## Re-capture every disassembly listing (needs both cross compilers)
	$(PYTHON) -m bench.run_disasm

.PHONY: bench-board
bench-board:  ## Re-run every host-target measurement. ON THE MACHINE BEING MEASURED ONLY.
	@$(PYTHON) -c 'import sys; sys.path.insert(0, "."); from bench.stamp import classify_machine; \
	  k = classify_machine(); sys.exit(0) if k == "board" else (print(f"Refusing to run: this is a {k!r} machine, not the board.\n" \
	  "Host-target figures are measured natively on the machine itself. Emulated timings are not\n" \
	  "measurements, and the book does not print them. See ch00.", file=sys.stderr) or sys.exit(1))'
	$(PYTHON) -m bench.run_setup --target host
	$(PYTHON) -m bench.run_measuring
	$(PYTHON) -m bench.run_hierarchy
	@echo
	@echo "Now re-render and commit:"
	@echo "  $(PYTHON) scripts/render-figures.py && git add bench/results chapters/_generated"
	@echo
	@echo "Figures still waiting on a runner that has not been written yet:"
	@$(PYTHON) -c 'import sys; sys.path.insert(0, "."); \
	  from tests.test_board import RUNNER_NOT_WRITTEN; \
	  print("  " + ", ".join(sorted(RUNNER_NOT_WRITTEN)) if RUNNER_NOT_WRITTEN else "  none")'

.PHONY: figures
figures:  ## Re-render every table, listing and diagram from committed results
	$(PYTHON) scripts/render-figures.py

# -- the book ----------------------------------------------------------------------------

.PHONY: book
book:  ## Live preview at localhost:3000
	myst start

.PHONY: pdf
pdf:  ## Build the whole book as one PDF
	$(PYTHON) scripts/build-pdf.py

.PHONY: test
test:  ## Run the test suite (board-only tests skip themselves)
	$(PYTHON) -m pytest tests/ -q

.PHONY: check
check:  ## Everything CI runs
	./scripts/ci-check.sh

.PHONY: clean
clean:  ## Remove build output; committed results and figures are kept
	rm -rf _build sysfs/build xv6/stage
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
