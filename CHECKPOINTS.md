# Checkpoints

Every chapter that changes the companion code gets a git tag, so you can start reading anywhere
and have exactly the code that chapter assumes.

```bash
git checkout ch07-vm       # the repository as it stood at the end of chapter 7
```

A tag is created when a chapter is finished — when `[DRAFT]` comes out of its title. Rows without
a tag in the repository yet are planned, not published.

| Chapter | Tag | What the code does at that point |
|---|---|---|
| ch00 | `ch00-setup` | Both targets working; the stamping, staging and figure machinery; `sysprobe` on both targets |
| ch01 | `ch01-whole-stack` | `sysfs/tools/stages.sh`, the two-route sum, and `sameanswer` on both targets |
| ch02 | `ch02-bits` | `sysfs/lib/bits.c` — the bit operations, tested; `signedness.c`, the four functions ch02 reads |
| ch03 | `ch03-c` | `sysfs/lib/addresses.c` — the pairs ch03 compiles against each other |
| ch04 | `ch04-asm` | `sysfs/tools/framewalk.c` — walk a stack from a frame pointer |
| ch05 | `ch05-elf` | `sysfs/tools/elfdump.c` — an ELF reader, written not described |
| ch06 | `ch06-traps` | First kernel patches: syscall counting and tracing |
| ch07 | `ch07-vm` | Page-table dumper; `sysfs/tools/sv39.c` |
| ch08 | `ch08-faults` | Lazy allocation and copy-on-write, with reference counting |
| ch09 | `ch09-devices` | Per-source interrupt counters; a driver for a simple device |
| ch10 | `ch10-locks` | Lock contention counters |
| ch11 | `ch11-sched` | Context-switch counters and per-process accounting |
| ch12 | `ch12-fs` | Block-I/O tracing through all seven layers |
| ch13 | `ch13-bridge` | The bridge program, built for both targets from one source |
| ch14 | `ch14-measuring` | `sysfs/lib/timing.c` — the book's clock. **Joins `CORE_SOURCES` here** |
| ch15 | `ch15-memory` | `pointer_chase.c`, `stride.c` — the hierarchy, measured |
| ch16 | `ch16-optimising` | `loops.c` — the transformation set |
| ch17 | `ch17-cpu` | `branches.c`, `ilp.c` |
| ch18 | `ch18-concurrency` | `sharing.c`, `atomics.c` — four cores, and what they cost each other |
| ch19 | `ch19-os-cost` | `syscall.c`, `fault.c`, `switch.c` |
| ch20 | `ch20-profiling` | `profile.sh`, and the program to diagnose with it |
| ch21 | `ch21-vectors` | `sysfs/bench/vectorisable.c` — loops that do and do not auto-vectorise |
| — | `v1.0` | Appendices complete, every figure measured, errata reconciled |

## Two tags that mean something different

`ch14-measuring` is the only tag that invalidates earlier results. The timing library joins
`bench.stamp.CORE_SOURCES` there, which changes the fingerprint of every `host` result in the
book. That is intentional, it happens exactly once, and the commit that does it regenerates
everything on the board.

`v1.0` is not a chapter. It is the point at which every `pending=` figure has landed, Appendix C
has been generated from the board, and `ERRATA.md` has nothing outstanding.

## Making one

```bash
./scripts/ci-check.sh                     # must be clean
git tag -a ch07-vm -m "ch07 — Virtual Memory"
git push origin ch07-vm
```

Then update the row above in the same commit as the chapter, so the table and the repository
cannot disagree.
