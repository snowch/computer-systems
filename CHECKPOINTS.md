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
| ch01 | `reading-c` | `sysfs/lib/declarations.c` — what `p + 1` and `->` become |
| ch02 | `c-without-a-runtime` | `bench/run_kernelc.py` — what the kernel does without a library |
| ch03 | `c-for-people-who-will-read-a-kernel` | `sysfs/lib/addresses.c` — the pairs ch03 compiles against each other |
| ch04 | `a-trap-with-nothing-else` | `bare/trap.c` — a trap with no operating system under it |
| ch05 | `interrupts-and-privilege` | `bare/timer.c`, `bare/privilege.c` — the CLINT, and a refusal |
| ch06 | `one-page-table-two-harts` | `bare/paging.c`, `bare/harts.c` — one mapping, and two cores |
| ch07 | `a-system-call-of-your-own` | `bare/syscall.c` — a number, arguments, a result, a dispatch |
| ch08 | `a-small-integer-that-means-a-device` | `bare/descriptors.c` — one table, two backends, and `read`/`write` through it |
| ch09 | `fork-built-rather-than-read` | `bare/fork.c` — a process table, a copied address space, two of them |
| ch10 | `what-a-computer-does-with-a-program` | `sysfs/tools/stages.sh`, the two-route sum, and `sameanswer` on both targets |
| ch11 | `representing-information` | `sysfs/lib/bits.c` — the bit operations, tested; `signedness.c`, the four functions ch11 reads |
| ch12 | `machine-level-code-on-riscv` | `sysfs/tools/framewalk.c` — walk a stack from a frame pointer; `sysfs/lib/frames.c` |
| ch13 | `linking-and-loading` | `sysfs/tools/elfdump.c` — an ELF reader with no `<elf.h>` in it |
| ch14 | `traps-and-system-calls` | First kernel patch: the per-cause trap census, printed on Ctrl-T |
| ch15 | `virtual-memory` | Page-table dumper; `sysfs/tools/sv39.c` |
| ch16 | `page-faults-as-a-feature` | Lazy allocation and copy-on-write, with reference counting |
| ch17 | `interrupts-and-drivers` | Per-source interrupt counters; a driver for a simple device |
| ch18 | `locks-and-memory-ordering` | Lock contention counters |
| ch19 | `scheduling-and-context-switches` | Context-switch counters and per-process accounting |
| ch20 | `the-file-system` | Block-I/O tracing through all seven layers |
| ch21 | `the-same-program-on-both-targets` | The bridge program, built for both targets from one source |
| ch22 | `measuring` | `sysfs/lib/timing.c` — the book's clock. **Joins `CORE_SOURCES` here** |
| ch23 | `the-memory-hierarchy` | `pointer_chase.c`, `stride.c` — the hierarchy, measured |
| ch24 | `optimising-code` | `loops.c` — the transformation set |
| ch25 | `the-cpu` | `branches.c`, `ilp.c` |
| ch26 | `memory-ordering-on-real-hardware` | `sharing.c`, `atomics.c` — four cores, and what they cost each other |
| ch27 | `the-os-layers-cost` | `syscall.c`, `fault.c`, `switch.c` |
| ch28 | `whole-machine-profiling` | `profile.sh`, and the program to diagnose with it |
| ch29 | `vectors` | `sysfs/bench/vectorisable.c` — loops that do and do not auto-vectorise |
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
