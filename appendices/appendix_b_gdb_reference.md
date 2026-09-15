---
title: "Appendix B — gdb for Kernels and RISC-V"
short_title: "Appendix B"
---

(appendix-b)=
# Appendix B · gdb for Kernels and RISC-V

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

Every sequence on this page has been run against this repository's own `make xv6-gdb`, on the
submodule at its pinned commit. Where something does not work, that is recorded too, because the
things that do not work are what cost the afternoon.

## Getting attached

Two terminals. In the first:

```bash
make xv6-gdb
```

That stages the kernel, builds it, and starts QEMU halted before its first instruction with a
debug stub listening. In the second:

```bash
gdb-multiarch xv6/stage/kernel/kernel
```

and then, inside gdb:

```
set architecture riscv:rv64
directory xv6/stage
target remote localhost:26000
```

**`gdb-multiarch`, not `gdb`.** This is the first thing that goes wrong and it goes wrong quietly.
A distribution's plain `gdb` is on every `PATH` and is almost always built for the host
architecture only. It connects to QEMU quite happily, and then fails on the first register read
with

```
Truncated register 37 in remote 'g' packet
```

which does not mention architectures at all. `scripts/verify-setup.py` asks each debugger it finds
whether it understands `riscv:rv64` rather than trusting its name, so `make verify` will tell you
before you start.

**`directory xv6/stage`.** The kernel is built in the staging tree and you are running gdb from the
repository root, so without this every stop reports `No such file or directory` and shows you no
source. It is not that the debug information is missing; it is that the paths in it are relative to
somewhere else.

**The terminal will look frozen, and it is not.** `make xv6-gdb` starts QEMU halted before the
first instruction, so there is no boot log and no prompt — that is the `-S` doing its job. `Ctrl-A`
then `C` switches to QEMU's monitor, where `info registers` answers and confirms the machine is
alive and stopped; `Ctrl-A` then `C` returns. `Ctrl-A` then `X` exits, and works whether or not
gdb is attached.

**Port 26000.** Not 1234. xv6's own `.gdbinit` template says 1234 and this repository does not use
it, because a fixed well-known port is a good way to attach to somebody else's QEMU.

## One hart, unless you mean it

```bash
python3 scripts/xv6-run.py --gdb --cpus 1
```

With the default number of harts, a breakpoint in shared kernel code is hit by whichever one gets
there, and gdb switches threads under you:

```
[Switching to Thread 1.2]

Thread 2 hit Breakpoint 1, _entry () at kernel/entry.S:12
```

That is real and sometimes it is the thing you are studying, but it makes every other
investigation harder. `info threads` lists them; `thread 2` moves; `--cpus 1` makes the question
go away.

## Stopping in a trap

The sequence [ch13](#traps-and-system-calls) is written around:

```
break usertrap
continue
printf "scause=%#lx sepc=%#lx stval=%#lx\n", $scause, $sepc, $stval
```

which prints, on the first system call of the boot:

```
scause=0x8 sepc=0x392 stval=0
```

`scause` 8 is an environment call from user mode; `sepc` is a user-mode address, which is the
thing worth noticing — you are in the kernel, and the register holding "where we were" holds an
address in a different address space. `stval` is zero because a system call has no faulting
address; [ch15](#page-faults-as-a-feature) is where it stops being zero.

CSRs are read as gdb convenience registers with a `$` in front, exactly like the integer ones.
Appendix A lists the ones this book uses.

```
print/x $satp
$1 = 0x8000000000087fff
```

The top nibble is the mode field: `8` is Sv39. The bottom forty-four bits are the physical page
number of the root page table, which is where [ch14](#virtual-memory)'s walk starts.

## When the stack is nonsense

Stopped in `usertrap`, a backtrace looks like this:

```
#0  usertrap () at kernel/trap.c:167
#1  0x0000003ffffff09c in ?? ()
```

The second frame is not corrupt and gdb is not confused. It is the trampoline, and gdb cannot name
it for a reason worth understanding.

**A breakpoint on `uservec` never fires.**

```
print/x &uservec
$1 = 0x80007000
```

That is where the linker put it. It is not where it executes. The trampoline page is mapped a
second time, at the top of every address space, and the trap path runs from *that* mapping — which
is the whole point of it existing, since the page table changes in the middle. Break on the symbol
and you will wait for ever.

Break on the address it actually runs at instead:

```
break *0x3ffffff000
continue
x/4i $pc
```

```
=> 0x3ffffff000:	csrw	sscratch,a0
   0x3ffffff004:	lui	a0,0x2000
   0x3ffffff008:	addiw	a0,a0,-1
   0x3ffffff00a:	slli	a0,a0,0xd
```

That address is `TRAMPOLINE` from `kernel/memlayout.h` — the last page below `MAXVA`. The `#1`
frame in the backtrace above is the same page plus an offset, which is how you recognise it.

Inside there, `bt` shows one frame and nothing else, because there is no frame: no prologue has
run, `sp` still belongs to the interrupted program, and the calling convention [ch11](#machine-level-code-on-riscv)
describes is not in force. **What to use instead**: `x/i $pc` to see where you are,
`info registers` to see the state, and the source of `trampoline.S` open beside it. Single-step
with `stepi`, never `step`, since there is no line table to step through.

The same applies anywhere before a stack is established — `entry.S`, `start.c`'s early lines, and
any point during a context switch.

## Watchpoints

Hardware watchpoints work, and on a kernel they are often the fastest way to answer "who wrote
this":

```
watch ticks
continue
```

```
Hardware watchpoint 3: ticks

Old value = 1
New value = 2
clockintr () at kernel/trap.c:305
305	    wakeup(&ticks);
```

**On a physical address** rather than a symbol, cast a literal:

```
watch *(unsigned long *)0x80000000
```

This is the form to use when the thing you care about has no name — a page you just allocated, a
device register, a slot in a page table. Note that it watches the address, so if the page table
changes underneath it you are now watching something else.

**Delete before you re-break.** A stale breakpoint in commonly-executed code will catch every
`continue` and make it look as though your new one never fires. `delete` with no argument clears
them all; `info breakpoints` says what is set.

## A scripted session

For anything you will run more than once, put the commands in a file and pass it with `-x`. This
is how every sequence on this page was checked:

```bash
gdb-multiarch -q -nx --batch -x session.gdb xv6/stage/kernel/kernel
```

`--batch` runs the file and exits, `-nx` ignores any `.gdbinit` you happen to have, and `-q`
drops the banner. Add `set confirm off` and `set pagination off` at the top of the file or it will
stop and wait for a keypress with nobody there.

## What this cannot tell you

**Anything about time.** gdb stops the machine. Every duration observed under it is a duration of
the debugger, and this is the `xv6` target, where a duration means nothing anyway ([ch00](#prerequisites-and-setup)).

**What the hardware would have done.** QEMU implements the architecture, not a pipeline. Stepping
through `uservec` shows you the instructions in order; a real core does not execute them in that
order, and [ch24](#the-cpu) is the chapter about the difference.

**Whether your change is correct.** A debugger shows one run. The problems in this book are tests
for the same reason: a run you watched go right is much weaker evidence than a check that fails
when it goes wrong.
