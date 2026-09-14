# Systems From Scratch

> **From bits to cycles, measured on RISC-V.**

📖 **Read it: <https://snowch.github.io/computer-systems/>** ·
📄 [Download the whole book as a PDF](https://snowch.github.io/computer-systems/systems-from-scratch.pdf)

A self-study text on computer systems and performance, organised around one question at every
layer of the stack:

**Where do the cycles go, and how would I know?**

Data representation, machine code, the memory hierarchy, the operating system layer, CPU
microarchitecture, whole-machine profiling — each taken apart on a teaching kernel you can stop
mid-trap, then measured on real RISC-V hardware.

## Status

**Scaffold complete; chapter 0 written.** The pipeline works end to end: both targets build and
run, the measurement machinery stamps and verifies, the site and the PDF build, and CI checks all
of it. Chapters 1–21 are stubs carrying their target, their question and the measurements they owe.

- **[PLAN.md](PLAN.md)** — the outline, per-chapter objectives and required measurements, hardware
  strategy, and the settled decisions.
- **[AUTHORING_GUIDE.md](AUTHORING_GUIDE.md)** — how to write a chapter here.
- **[CHECKPOINTS.md](CHECKPOINTS.md)** — the per-chapter tag scheme.
- **[ORIGINALITY.md](ORIGINALITY.md)** — per chapter, how it differs from the works nearest it.
- **[ERRATA.md](ERRATA.md)** — corrections, and the gaps that are known rather than accidental.

## Two targets

| Target | What | For |
|---|---|---|
| **`xv6`** | The MIT teaching kernel under `qemu-system-riscv64` | What a program *does*: system calls, page tables, scheduling, on-disk state. Runs anywhere. |
| **`host`** | An RV64GC Linux board with working `perf` counters, natively over SSH — see [`hardware/`](hardware/) | What a program *costs*: cycles, cache misses, mispredictions, cores interfering. |

QEMU models no cache, no branch predictor and no pipeline, so it will answer a question about
nanoseconds and the answer will be fiction. The repository enforces the split rather than trusting
anyone to remember it: `make bench-board` refuses to run off the board, and
`scripts/verify-numbers.py` rejects a `host` figure that was not measured natively and any `xv6`
result containing a duration.

## Getting started

```bash
git clone --recursive https://github.com/snowch/computer-systems.git
cd computer-systems
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 scripts/verify-setup.py     # says which targets this machine can run
```

On a laptop with a RISC-V cross compiler and QEMU, that is everything Parts I and II need —
fourteen chapters. Part III needs a RISC-V board; **[`hardware/`](hardware/)** says what it has to
be able to do, and carries a prompt you can hand to an assistant to find one that is actually in
stock where you are. The book deliberately does not name a part number — it outlives any
listing — and `verify-setup.py` is what decides whether the board you bought can do the job.

```bash
make xv6-qemu      # boot the teaching kernel
make bench-xv6     # re-run every xv6-target measurement
make check         # everything CI runs
make book          # live preview of the site
```

`make` on its own lists the rest.

## How the numbers work

Every figure traces to a JSON file under `bench/results/` recording the target, the board or QEMU
version, the kernel, the compiler, its flags, and a content hash of the code that produced it. No
number is typed into prose, and CI fails when a quoted figure's hash stops matching the code in
the repository.

Where a measurement has not been taken, the book shows a box saying so — never a placeholder
number. Where the hardware cannot answer a question at all, the chapter says that and shows the
reasoning it used instead.

## Problems

Every chapter ends with problems, and every problem is a stub under `tests/` with a test that
passes only when you have solved it. There is no answer key in the back, which means there is no
answer key to be wrong.

```bash
python3 -m pytest tests/ch00 -q
```

## Licence

Split. The book text — `index.md`, `chapters/`, `appendices/` and the project documentation — is
[CC-BY-NC-4.0](LICENSE). The code — `sysfs/`, `bench/`, `tests/`, `scripts/`, `xv6/apps/` — is
[Apache-2.0](LICENSE-CODE), so it can actually be reused. xv6 itself is a git submodule of
[mit-pdos/xv6-riscv](https://github.com/mit-pdos/xv6-riscv) and keeps its own MIT licence; the
diffs in `xv6/patches/` are offered under the same terms. See [xv6/README.md](xv6/README.md).
