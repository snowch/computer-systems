# Checkpoints

Every chapter that changes the companion code gets a git tag, so you can start reading anywhere
and have exactly the code that chapter assumes.

```bash
git checkout virtual-memory       # the repository as it stood at the end of chapter 7
```

A tag is created when a chapter is finished — when `[DRAFT]` comes out of its title. Rows without
a tag in the repository yet are planned, not published.

| Chapter | Tag | What the code does at that point |
|---|---|---|
| ch00 | `prerequisites-and-setup` | Both targets working; the stamping, staging and figure machinery; `sysprobe` on both targets |
| ch01 | `reading-a-listing` | `sysfs/lib/shapes.c` and its listing on both instruction sets, captured by `bench/run_disasm.py` |
| ch02 | `memory-is-one-array` | `sysfs/lib/declarations.c` — what `p + 1` and `->` become |
| ch03 | `c-without-a-runtime` | `bench/run_kernelc.py` — what the kernel does without a library |
| ch04 | `c-for-people-who-will-read-a-kernel` | `sysfs/lib/addresses.c` — the pairs ch03 compiles against each other |
| ch05 | `a-trap-with-nothing-else` | `bare/trap.c` — a trap with no operating system under it |
| ch06 | `interrupts-and-privilege` | `bare/timer.c`, `bare/privilege.c` — the CLINT, and a refusal |
| ch07 | `one-page-table-two-harts` | `bare/paging.c`, `bare/harts.c` — one mapping, and two cores |
| ch08 | `a-system-call-of-your-own` | `bare/syscall.c` — a number, arguments, a result, a dispatch |
| ch09 | `a-small-integer-that-means-a-device` | `bare/descriptors.c` — one table, two backends, and `read`/`write` through it |
| ch10 | `fork-built-rather-than-read` | `bare/fork.c` — a process table, a copied address space, two of them |
| ch11 | `what-a-computer-does-with-a-program` | `sysfs/tools/stages.sh`, the two-route sum, and `sameanswer` on both targets |
| ch12 | `representing-information` | `sysfs/lib/bits.c` — the bit operations, tested; `signedness.c`, the four functions ch11 reads |
| ch13 | `machine-level-code-on-riscv` | `sysfs/tools/framewalk.c` — walk a stack from a frame pointer; `sysfs/lib/frames.c` |
| ch14 | `linking-and-loading` | `sysfs/tools/elfdump.c` — an ELF reader with no `<elf.h>` in it |
| ch15 | `traps-and-system-calls` | First kernel patch: the per-cause trap census, printed on Ctrl-T |
| ch16 | `virtual-memory` | Page-table dumper; `sysfs/tools/sv39.c` |
| ch17 | `page-faults-as-a-feature` | Lazy allocation and copy-on-write, with reference counting |
| ch18 | `interrupts-and-drivers` | Per-source interrupt counters; a driver for a simple device |
| ch19 | `locks-and-memory-ordering` | Lock contention counters |
| ch20 | `scheduling-and-context-switches` | Context-switch counters and per-process accounting |
| ch21 | `the-file-system` | Block-I/O tracing through all seven layers |
| ch22 | `the-same-program-on-both-targets` | The bridge program, built for both targets from one source |
| ch23 | `measuring` | `sysfs/lib/timing.c` — the book's clock. **Joins `CORE_SOURCES` here** |
| ch24 | `the-memory-hierarchy` | `pointer_chase.c`, `stride.c` — the hierarchy, measured |
| ch25 | `optimising-code` | `loops.c` — the transformation set |
| ch26 | `the-cpu` | `branches.c`, `ilp.c` |
| ch27 | `memory-ordering-on-real-hardware` | `sharing.c`, `atomics.c` — four cores, and what they cost each other |
| ch28 | `the-os-layers-cost` | `syscall.c`, `fault.c`, `switch.c` |
| ch29 | `whole-machine-profiling` | `profile.sh`, and the program to diagnose with it |
| ch30 | `vectors` | `sysfs/bench/vectorisable.c` — loops that do and do not auto-vectorise |
| — | `v1.0` | Appendices complete, every figure measured, errata reconciled |

## Two tags that mean something different

`measuring` is the only tag that invalidates earlier results. The timing library joins
`bench.stamp.CORE_SOURCES` there, which changes the fingerprint of every `host` result in the
book. That is intentional, it happens exactly once, and the commit that does it regenerates
everything on the board.

`v1.0` is not a chapter. It is the point at which every `pending=` figure has landed, Appendix C
has been generated from the board, and `ERRATA.md` has nothing outstanding.

## Making one

```bash
./scripts/ci-check.sh                     # must be clean
git tag -a virtual-memory -m "ch15 — Virtual Memory"
git push origin virtual-memory
```

Then update the row above in the same commit as the chapter, so the table and the repository
cannot disagree.
