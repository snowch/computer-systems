# The xv6 target

Three directories, and the split between them is the point.

```
xv6/
├── xv6-riscv/     git submodule of mit-pdos/xv6-riscv. Upstream. Never modified.
├── apps/          the book's own xv6 user programs. Apache-2.0.
├── patches/       the book's kernel instrumentation, as diffs. MIT, like what they patch.
└── stage/         generated. The three above, combined. Not in git.
```

## Why a submodule and not a fork

xv6 is MIT-licensed, so copying it into this repository would be legal. It would also be a lie
about what the book is doing. A reader needs to be able to see, exactly, what this book changed
about the kernel — and a copied tree hides that in a diff nobody will run. A submodule plus a
patch directory makes it a question with an answer:

```bash
ls xv6/patches/          # everything this book changes about the kernel
git -C xv6/xv6-riscv status --porcelain   # always empty, and a test asserts it
```

It also means upstream's history stays legible. When xv6 moves, a patch that no longer applies
fails loudly with the file and hunk that moved, which is information; a merge conflict in a
vendored tree is not.

## How a build happens

`scripts/xv6-run.py` (and `bench.xv6.prepare`) assembles `xv6/stage`:

1. copy the submodule, minus its `.git`;
2. copy `sysfs/include/sysfs/*.h` to `stage/sysfs/`, so a program can
   `#include "sysfs/probe.h"` — xv6 already compiles with `-I.`;
3. copy `apps/*.c` into `stage/user/` and add them to the staged Makefile's `UPROGS`;
4. apply `patches/*.patch` in filename order with `git apply`.

Staging is skipped when nothing that feeds it has changed, so the common case costs nothing.
`make xv6-clean` deletes the staging tree; the submodule is never touched by any of it.

Registering user programs is done by editing the `UPROGS` list mechanically rather than by a
patch. A patch against a list of filenames breaks the next time upstream adds a program of its
own, and "does not apply" would tell you nothing about what you wanted.

## Writing a patch

Patches are ordinary `git diff` output against the pinned submodule commit. Name them
`NN-what-it-does.patch` so the order is visible:

```bash
make xv6-clean && make xv6-build        # a clean staging tree
cd xv6/stage && git init -q && git add -A && git commit -qm base
# ... edit the kernel ...
git diff > ../patches/13-trace-syscalls.patch
```

Each patch gets a comment block at the top saying which chapter introduced it and what it
measures. Keep them small and independent: a patch that changes three subsystems cannot be read
alongside the chapter that explains one of them.

## What this target is for

Structure, not time. QEMU executes RISC-V correctly and models nothing about the cost of doing
so — no caches, no branch predictor, no pipeline, no memory latency. `bench/stamp.py` refuses to
record a duration in an `xv6` result for that reason, and `scripts/verify-numbers.py` fails the
build if one appears. Everything about cost is measured on the board (`make bench-board`).

## Licence

The submodule is MIT, © Russ Cox, Frans Kaashoek and Robert Morris, and carries its own
`LICENSE`. Files in `patches/` are diffs against MIT-licensed sources and are offered under the
same terms. Files in `apps/` are the book's own and are Apache-2.0, like the rest of the code
here — see `LICENSE-CODE`.
