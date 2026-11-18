---
title: "11 · fork, Built Rather Than Read"
short_title: "11 · fork, Built Rather Than Read"
---

(fork-built-rather-than-read)=
# 11 · fork, Built Rather Than Read

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `bare` — a RISC-V machine in QEMU without an operating system |
| **Prerequisites** | [ch10](#a-small-integer-that-means-a-device) |
| **Evidence** | Parent and child return values, and pages copied in the example and in xv6. |
:::

## The question

What is the least a machine needs before two programs can run on it?

`fork` is usually introduced as a riddle: a function that returns twice, with different answers. It
is not a riddle. It looks like one because it is normally met from the outside. From the inside it
is a short function, and the two returns stop being mysterious once you can see that a return value
is a word in a saved register set.

Everything this chapter needs already exists. [ch08](#one-page-table-two-harts) built an
*address space* — a page table, and so a private view of memory;
[ch09](#a-system-call-of-your-own) saved a caller's registers into a frame. A process is those
two things kept together, and `fork` is a copy.

(fork-built-rather-than-read-example)=
## Make the parent and child return separately

### What a process is, here

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: struct proc {
:end-before: static struct proc procs
```

A saved register set, a place it was, and an address space. That is the whole of it — and the first
field is [ch09](#a-system-call-of-your-own)'s trap frame, unchanged. The frame was built to survive
a system call; keep it a little longer and it is a saved process.

### Mapping one page rather than one gigabyte

[ch08](#one-page-table-two-harts) got away with three top-level leaf entries. A per-process page
needs a real walk — an entry at each of the three levels — because four kilobytes is a leaf at
the bottom level, and the levels above it have to exist first:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: /* Walk to the leaf entry for one virtual address
:end-before: static uint64 *build_address_space
```

Each process gets the kernel's identity mappings — without them the code would vanish the moment
its own table was installed — plus one page of its own at the same virtual address:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: static uint64 *build_address_space(uint64 *user_page)
:end-before: static int fork_current
```

Same address in both processes, different physical page behind it. That is what "its own memory"
means, mechanically, and it is why an address space is worth having.

### fork

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: static int fork_current(uint64 *frame)
:end-before: uint64 bare_syscall
```

The frame is copied wholesale and then one slot is changed, and that one line is why `fork` returns
twice. Slot ten is `a0`, where a system call's return value lives, and the child resumes by having
its frame loaded back into the registers. Two frames, identical but for one word, produce two
returns with different answers.

The page is copied too — a fresh page and a byte-for-byte duplicate, so the child begins with
everything the parent had and can then diverge. This is the eager version, and it is what xv6's
`uvmcopy` does too: a fresh page and a copy, per page, at the moment of the call.
[ch18](#page-faults-as-a-feature) is where that stops being necessary.

### Putting a process back on the processor

```{literalinclude} ../sysfs/bare/syscalls.c
:language: c
:start-at: /* Put a saved process back on the processor: its registers, and where it was.
:end-before: }
```

`sp` is loaded last because every other load is relative to it, and a frame stops being addressable
the instant you replace the pointer to it.

The scheduler is four lines, and calling it a scheduler is generous:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at: void bare_process_left(void)
:end-before: int main(void)
```

Install the next process's address space, load its registers, `mret`. There is no policy, no
priority and no preemption — nothing takes the processor away from a process that has not given
it up. [ch21](#scheduling-and-context-switches) is where the interesting parts go back in.

### The kernel cannot simply dereference what it is given

One detail here is a genuine trap, and it cost a confusing hour:

```{literalinclude} ../sysfs/bare/fork.c
:language: c
:start-at:     /* The handler runs in machine mode, and machine mode ignores `satp`.
:end-before:     default:
```

The handler runs in machine mode, and [ch08](#one-page-table-two-harts) established that machine
mode ignores `satp`. So an address the caller supplies is not an address the handler can use — and
on this machine the particular number involved lands in a region QEMU reserves for PCI devices,
which answers every read with ones, so the failure is not even a fault. It is a plausible-looking
wrong answer.

A real kernel walks the caller's page table to translate by hand. That function is called `copyin`,
and this is why it exists.

## What we measured

From your checkout, run the supplied bare-metal `fork` program:

```bash
./run fork
```

Compare `parent_result` and `child_result`. Then compare `child_inherited` with `parent_after`
and check `childs_write_stayed_in_its_own_page`. What evidence shows the child received a copy
of the parent’s data and could change its own copy independently?

```{include} _generated/fork-built-rather-than-read-fork.md
```

One page copied, for one page mapped. xv6 copies every mapped page of the parent the same way —
`kalloc` and `memmove` per page, no sharing — so the count here is small for the same reason the
program is small, not because the strategy differs.

## What this cannot tell you

**What `fork` costs.** Copying a page has a price, copying a thousand has a much larger one, and
the entire reason real kernels stopped doing this eagerly is a number this target cannot produce.
[ch29](#the-os-layers-cost) measures a real `fork`, and the gap between an eager copy and what
Linux actually does is most of the answer.

**What the child should inherit.** The child here gets the address space and nothing else, because
there is nothing else. A real `fork` has to decide about descriptors, the working directory,
signal handlers, resource limits and more. [ch10](#a-small-integer-that-means-a-device)'s two
tables answer the descriptor half: the descriptor table is copied, the open files it refers to are
shared.

**Whether two processes really run concurrently.** They do not. One runs, gives up, and the other
starts. Nothing here preempts anything, and both are on one hart.

**What happens when the table is full.** There is room for two, `fork` is called once, and the
question of what a process table does when it runs out is left entirely alone. xv6's `allocproc`
returns zero; what the caller should do about it is a design question this program never has to
face.

## Problems

Use the files below in your local checkout. Run each test command from the repository root.

**11.1 — Make the child run first.**
Open `tests/fork_built_rather_than_read/problem_1_child_first.py`. Copy `sysfs/bare/fork.c` to
`tests/fork_built_rather_than_read/answer_child_first.c`. Change when the parent resumes so
the child prints first. The test checks the order and both return values.

```bash
python3 -m pytest tests/fork_built_rather_than_read/test_problem_1_child_first.py
```

**11.2 — Run out of processes.**
Open `tests/fork_built_rather_than_read/problem_2_full_table.py`. Choose a return value for a
full process table. Implement the case in `tests/fork_built_rather_than_read/answer_full.c`,
starting from `sysfs/bare/fork.c`. Show the caller handling the failure and print the values
specified in the stub.

```bash
python3 -m pytest tests/fork_built_rather_than_read/test_problem_2_full_table.py
```

**11.3 — Count what a lazy fork would save.**
Open `tests/fork_built_rather_than_read/problem_3_lazy.py`. Predict which operations copy-on-
write would avoid, what the handler would need to do, and the fault and page-table bit
involved. In `tests/fork_built_rather_than_read/answer_lazy.c`, report the count of pages the
original copies using the format specified in the stub.

```bash
python3 -m pytest tests/fork_built_rather_than_read/test_problem_3_lazy.py
```

## Where to go next

The privileged specification @riscv-isa-privileged has the page-table entry bits this program sets by hand,
including the one problem 11.3 asks about.

This is the end of [Part II](#part2). [Part III](#part3) steps back to ask what a program *is*
before [Part IV](#part4) reads a kernel — and that kernel's `fork` will look like a longer version
of this one rather than a new idea, which was the point of building it.
