---
title: "Appendix G — Reading xv6 Alongside This Book"
short_title: "Appendix G"
---

(appendix-g)=
# Appendix G · Reading xv6 Alongside This Book

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

Everything below was read out of the submodule at its pinned commit rather than recalled, so it
describes the code you have checked out. [Appendix D](#appendix-d) says what else is in that tree.

## The two books ask different questions

The kernel this book uses has its own commentary @xv6-book, written by the people who wrote the
kernel, distributed free by MIT. It is the best available explanation of what that code does and
you should read it.

It is not a competitor and this book does not summarise it. They ask different questions of the
same source:

| | |
|---|---|
| **The xv6 commentary** | What does this code do, and why is it arranged this way? |
| **This book** | What does it cost, and how would I know? |

That difference decides almost everything about how the two are organised. The commentary follows
the kernel's own structure, because it is explaining a program. This book follows a question, which
is why its [Part IV](#part4) takes the kernel apart mechanism by mechanism and its [Part V](#part5) then asks the
price of each — and why a mechanism that is one section there may be a chapter here, or the
reverse.

**Read them in either order.** A reader who has the commentary open will find this book's chapters
supply the measurements it does not attempt; a reader who starts here will find the commentary
supplies the surrounding code that a chapter about one mechanism does not show.

## Where the coverage meets

Mapped by topic rather than by chapter number, deliberately: the commentary's numbering shifts
between revisions and its topics do not.

| When the commentary is on | This book is in | And the price is in |
|---|---|---|
| Operating system interfaces — processes, `fork`, `exec`, files | [ch04](#c-without-a-runtime) for the memory model it implies; the trace below | — |
| Operating system organization, isolation, privilege | [ch16](#traps-and-system-calls) | [ch29](#the-os-layers-cost) |
| Page tables and Sv39 | [ch17](#virtual-memory) | [ch25](#the-memory-hierarchy) address translation, [ch29](#the-os-layers-cost) faults |
| Traps, system calls, and the trap path | [ch16](#traps-and-system-calls) | [ch29](#the-os-layers-cost) |
| Page faults and what can be built on them | [ch18](#page-faults-as-a-feature) | [ch29](#the-os-layers-cost) |
| Interrupts and device drivers | [ch19](#interrupts-and-drivers) | — |
| Locking | [ch20](#locks-and-memory-ordering) | [ch28](#memory-ordering-on-real-hardware) |
| Scheduling and context switching | [ch21](#scheduling-and-context-switches) | [ch29](#the-os-layers-cost) |
| File system, logging, buffer cache | [ch22](#the-file-system) | — |
| Concurrency revisited, memory ordering | [ch20](#locks-and-memory-ordering) | [ch28](#memory-ordering-on-real-hardware) |

Three rows have no price, and the reason is the same each time: the cost of an interrupt, a file
system and a driver on this machine is the cost of *this machine's* devices, and the reference
board's storage is an SD card behind a bridge rather than anything a chapter could generalise
from. [ch19](#interrupts-and-drivers) and [ch22](#the-file-system) say so in their own limitations sections.

## One call through every layer: `fork`

The worked example of how to use the table above, and the reason it is `fork`: it is the one call
in the kernel that touches almost every mechanism this book takes apart separately. Reading it is
the fastest way to see that the chapters are describing one system rather than six.

In the pinned tree the function is `kfork` in `kernel/proc.c` — `sys_fork` in `kernel/sysproc.c`
is a one-line wrapper. Older revisions of the commentary call it `fork`.

| What it does | Which layer | Where that is explained |
|---|---|---|
| `allocproc()` finds an unused slot in the fixed process table | allocation without a heap | [ch04](#c-without-a-runtime) |
| …and returns `0` when there is none, which becomes `-1` | failure that returns rather than raises | [ch04](#c-without-a-runtime), problem 2.2 |
| `uvmcopy()` walks the parent's page table and copies **every** page | address translation | [ch17](#virtual-memory) |
| …with a `kalloc()` per page, which can also fail | the physical allocator | [ch18](#page-faults-as-a-feature) |
| `*(np->trapframe) = *(p->trapframe)` copies the saved user registers | what a trap saves | [ch16](#traps-and-system-calls) |
| `np->trapframe->a0 = 0` | the calling convention | [ch14](#machine-level-code-on-riscv), [ch16](#traps-and-system-calls) |
| `filedup()` over the open files, and `idup()` on the working directory | reference counting | [ch22](#the-file-system) |
| `np->state = RUNNABLE` makes it eligible to be chosen | scheduling | [ch21](#scheduling-and-context-switches) |

**Why it returns twice** is the one line worth carrying away, and it is the fourth row. Nothing
returns twice. The child is a copy of the parent — including the saved register set the trap path
will restore on the way out — with a single word changed: the register the calling convention uses
for a return value. Both processes then resume at the instruction after the `ecall`, each reading
its own `a0`. [ch16](#traps-and-system-calls) is where that saved register set is counted.

**`uvmcopy` copies eagerly**, and the pinned tree is explicit about it: a `kalloc` and a `memmove`
of a whole page, per page, with no sharing. That is a deliberate simplification and it is what
makes [ch18](#page-faults-as-a-feature)'s copy-on-write material a change rather than an explanation — the mechanism
is absent here, so the chapter has somewhere to put it. A production kernel shares the pages and
marks them read-only, and [ch29](#the-os-layers-cost) is where the difference in cost is measured.

**The failure paths are the chapter's second problem, in the source.** `kfork` can fail in two
places — no free slot, or no free page — and both return `-1` after undoing what they had done. A
caller that does not look at the result has written the bug [ch04](#c-without-a-runtime) is about.

## What this cannot tell you

**What the commentary says.** This page is a map, not a summary, and it deliberately does not
restate a word of it. Where the two books cover the same mechanism they do it differently and both
are worth reading; where this page sends you to a chapter, the chapter is about the cost.

**Anything about a different revision.** The tree here is pinned, and in it the function is
`kfork` and `allocproc` returns `0`. Both have been spelled otherwise. The conditions line under
[Appendix D](#appendix-d)'s tables names the commit; `git -C xv6/xv6-riscv log -1` is the check.

**Whether the commentary's version and this one agree.** They are different documents at different
revisions, and where they differ the tree wins — the tree is what boots.
