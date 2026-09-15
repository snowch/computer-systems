# Checkpoints

Every chapter that changes the companion code gets a git tag, so you can start reading anywhere
and have exactly the code that chapter assumes.

```bash
git checkout ch14-vm       # the repository as it stood at the end of chapter 7
```

A tag is created when a chapter is finished — when `[DRAFT]` comes out of its title. Rows without
a tag in the repository yet are planned, not published.

| Chapter | Tag | What the code does at that point |
|---|---|---|
| ch00 | `ch00-setup` | Both targets working; the stamping, staging and figure machinery; `sysprobe` on both targets |
| ch01 | `ch01-reading-c` | `sysfs/lib/declarations.c` — what `p + 1` and `->` become |
| ch02 | `ch02-no-runtime` | `bench/run_kernelc.py` — what the kernel does without a library |
| ch03 | `ch03-c` | `sysfs/lib/addresses.c` — the pairs ch03 compiles against each other |
| ch04 | `ch04-bare-trap` | `bare/trap.c` — a trap with no operating system under it |
| ch05 | `ch05-bare-interrupt` | `bare/timer.c`, `bare/privilege.c` — the CLINT, and a refusal |
| ch06 | `ch06-bare-paging` | `bare/paging.c`, `bare/harts.c` — one mapping, and two cores |
| ch07 | `ch07-bare-syscall` | `bare/syscall.c` — a number, arguments, a result, a dispatch |
| ch08 | `ch08-bare-fork` | `bare/fork.c` — a process table, a copied address space, two of them |
| ch09 | `ch09-whole-stack` | `sysfs/tools/stages.sh`, the two-route sum, and `sameanswer` on both targets |
| ch10 | `ch10-bits` | `sysfs/lib/bits.c` — the bit operations, tested; `signedness.c`, the four functions ch10 reads |
| ch11 | `ch11-asm` | `sysfs/tools/framewalk.c` — walk a stack from a frame pointer; `sysfs/lib/frames.c` |
| ch12 | `ch12-elf` | `sysfs/tools/elfdump.c` — an ELF reader with no `<elf.h>` in it |
| ch13 | `ch13-traps` | First kernel patch: the per-cause trap census, printed on Ctrl-T |
| ch14 | `ch14-vm` | Page-table dumper; `sysfs/tools/sv39.c` |
| ch15 | `ch15-faults` | Lazy allocation and copy-on-write, with reference counting |
| ch16 | `ch16-devices` | Per-source interrupt counters; a driver for a simple device |
| ch17 | `ch17-locks` | Lock contention counters |
| ch18 | `ch18-sched` | Context-switch counters and per-process accounting |
| ch19 | `ch19-fs` | Block-I/O tracing through all seven layers |
| ch20 | `ch20-bridge` | The bridge program, built for both targets from one source |
| ch21 | `ch21-measuring` | `sysfs/lib/timing.c` — the book's clock. **Joins `CORE_SOURCES` here** |
| ch22 | `ch22-memory` | `pointer_chase.c`, `stride.c` — the hierarchy, measured |
| ch23 | `ch23-optimising` | `loops.c` — the transformation set |
| ch24 | `ch24-cpu` | `branches.c`, `ilp.c` |
| ch25 | `ch25-concurrency` | `sharing.c`, `atomics.c` — four cores, and what they cost each other |
| ch26 | `ch26-os-cost` | `syscall.c`, `fault.c`, `switch.c` |
| ch27 | `ch27-profiling` | `profile.sh`, and the program to diagnose with it |
| ch28 | `ch28-vectors` | `sysfs/bench/vectorisable.c` — loops that do and do not auto-vectorise |
| — | `v1.0` | Appendices complete, every figure measured, errata reconciled |

## Two tags that mean something different

`ch21-measuring` is the only tag that invalidates earlier results. The timing library joins
`bench.stamp.CORE_SOURCES` there, which changes the fingerprint of every `host` result in the
book. That is intentional, it happens exactly once, and the commit that does it regenerates
everything on the board.

`v1.0` is not a chapter. It is the point at which every `pending=` figure has landed, Appendix C
has been generated from the board, and `ERRATA.md` has nothing outstanding.

## Making one

```bash
./scripts/ci-check.sh                     # must be clean
git tag -a ch14-vm -m "ch14 — Virtual Memory"
git push origin ch14-vm
```

Then update the row above in the same commit as the chapter, so the table and the repository
cannot disagree.
