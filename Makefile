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

.PHONY: run
run:  ## List every program a reader can run (./run <name> runs one)
	@./run --list

.PHONY: bench-bare
bench-bare:  ## Re-run every bare-metal program (runs anywhere QEMU and the cross compiler do)
	$(PYTHON) -m bench.run_bare

.PHONY: bench-listings
bench-listings:  ## Re-capture every disassembly listing (needs both cross compilers)
	$(PYTHON) -m bench.run_disasm

# -- the pinned toolchain (deterministic results) ---------------------------------------
#
# Everything that is *not* a host timing — the listings, and the structural xv6 and bare results —
# is decided by the compiler version, not by hardware, so it must be reproduced with the exact gcc
# the committed results were captured with (13.3.0, Ubuntu 24.04). `Dockerfile` pins it. Host
# timings are never in here: they are `bench-board`, on real silicon.

IMAGE ?= sfs-toolchain

.PHONY: docker-image
docker-image:  ## Build the pinned-toolchain image (gcc 13.3.0, both cross targets, QEMU)
	docker build --platform linux/amd64 -t $(IMAGE) .

.PHONY: regen-deterministic
regen-deterministic:  ## Re-capture every non-host result with the pinned toolchain (run in the image)
	$(PYTHON) -m bench.run_setup --target xv6
	$(PYTHON) -m bench.run_disasm
	$(PYTHON) -m bench.run_stages
	$(PYTHON) -m bench.run_frames
	$(PYTHON) -m bench.run_elf
	$(PYTHON) -m bench.run_traps
	$(PYTHON) -m bench.run_pagetable
	$(PYTHON) -m bench.run_faults
	$(PYTHON) -m bench.run_interrupts
	$(PYTHON) -m bench.run_locks
	$(PYTHON) -m bench.run_switch
	$(PYTHON) -m bench.run_blocks
	$(PYTHON) -m bench.run_bridge
	$(PYTHON) -m bench.run_loops
	$(PYTHON) -m bench.run_pipeline
	$(PYTHON) -m bench.run_sharing
	$(PYTHON) -m bench.run_profile
	$(PYTHON) -m bench.run_firstc
	$(PYTHON) -m bench.run_kernelc
	$(PYTHON) -m bench.run_bare
	$(PYTHON) -m bench.run_filemap
	$(PYTHON) -m bench.run_vectors

.PHONY: docker-regen
docker-regen: docker-image  ## Build the image and re-capture every deterministic result inside it
	docker run --rm --platform linux/amd64 -v "$(CURDIR):/work" -w /work $(IMAGE) \
	  make regen-deterministic

.PHONY: bench-board
bench-board:  ## Re-run every host-target measurement. ON THE MACHINE BEING MEASURED ONLY.
	@$(PYTHON) -c 'import sys; sys.path.insert(0, "."); from bench.stamp import classify_machine; \
	  k = classify_machine(); sys.exit(0) if k == "board" else (print(f"Refusing to run: this is a {k!r} machine, not the board.\n" \
	  "Host-target figures are measured natively on the machine itself. Emulated timings are not\n" \
	  "measurements, and the book does not print them. See ch00.", file=sys.stderr) or sys.exit(1))'
	$(PYTHON) -m bench.run_setup --target host
	$(PYTHON) -m bench.run_measuring
	$(PYTHON) -m bench.run_hierarchy
	$(PYTHON) -m bench.run_bridgecost
	$(PYTHON) -m bench.run_loopcost
	$(PYTHON) -m bench.run_pipelinecost
	$(PYTHON) -m bench.run_vectorcost
	$(PYTHON) -m bench.run_sharingcost
	$(PYTHON) -m bench.run_oscost
	$(PYTHON) -m bench.run_profilecost
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
