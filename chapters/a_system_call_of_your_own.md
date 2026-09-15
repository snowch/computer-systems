---
title: "A System Call of Your Own"
short_title: "07 · A System Call of Your Own"
---

(a-system-call-of-your-own)=
# 07 · A System Call of Your Own

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [ch06](#one-page-table-two-harts) |
| **What it measures** | A call number, arguments and a return value crossing the boundary, and the count of registers this handler has to save once the caller is a stranger. |
:::

## The question

What has to exist before `ecall` is a system call rather than a trap?

[ch04](#a-trap-with-nothing-else) already executed an `ecall` and handled it. Nothing about that
was a system call: no request was made, nothing was asked for, and the handler had nothing to
decide. Four things are missing, and this chapter adds them — a number saying which call, somewhere
to put arguments, somewhere to put a result, and a dispatch. A fifth thing turns out to be missing
too, and it is the expensive one.

## The material

### The caller is now a stranger

ch04's handler could be careless because the compiler was not. It could see the handler and the
code it interrupted, knew which registers were live, and saved exactly those.

That arrangement is gone. The caller runs in supervisor mode, was compiled separately as far as
the boundary is concerned, and might be using any register for anything. So the handler saves all
of them:

```{literalinclude} ../sysfs/bare/syscall.c
:language: c
:start-at: /* The trap entry. Naked because every instruction in it matters
:end-before:         "addi sp, sp, -"
```

Thirty-one, not thirty-two, because `x0` is hard-wired to zero and has nothing to lose. It is
written out rather than generated because writing it out is the point: this is the cost of not
knowing your caller, and it is paid on every single call.

The frame also becomes the interface. Once the registers are in memory, "the arguments" and "the
registers" are the same thing, and the handler reads them as an array:

```{literalinclude} ../sysfs/bare/syscall.c
:language: c
:start-at: void syscall_dispatch(uint64 *frame) {
:end-before:     if (cause != CAUSE_ECALL_FROM_S)
```

`a7` holds the number and `a0` the first argument because those two lines say so. That is the
entire status of the calling convention at this point — a convention is an agreement, and here you
are both parties.

### The dispatch

```{literalinclude} ../sysfs/bare/syscall.c
:language: c
:start-at:     switch (number) {
:end-before:     case SYS_LEAVE:
```

Writing to `frame[10]` is how a result gets back: the epilogue restores `a0` from that slot, so the
caller finds it in the register the convention promised. Nothing returns anything in the C sense.

The default case is worth as much as the others:

```{literalinclude} ../sysfs/bare/syscall.c
:language: c
:start-at:     default:
:end-before:         break;
```

A number nobody implemented gets an error, not a stop. That is the difference between an interface
and a trapdoor, and it is a decision — the hardware would have been equally happy to let the
machine wander off.

### Calling it

From the other side, a system call is four register moves and an instruction:

```{literalinclude} ../sysfs/bare/syscall.c
:language: c
:start-at: static uint64 call(uint64 number, uint64 first, uint64 second)
:end-before: __attribute__((noinline)) static void user_of_the_interface
```

The `"+r"(a0)` is doing something worth noticing: it tells the compiler that `a0` is both an input
and an output, which is exactly the claim the convention makes. Get that wrong and the compiler
will cheerfully assume the register still holds what it put there.

## What we measured

```{include} _generated/a-system-call-of-your-own-syscall.md
```

Two of those rows are the same fact from opposite sides. `caller_register_in_frame` is the handler
finding the caller's `s2` in the saved frame; `caller_register_intact` is the caller finding it
still there afterwards. A handler that saved nothing would fail the second and never reach the
first.

## What this cannot tell you

**What a system call costs.** Thirty-one stores and thirty-one loads is a count, not a price, and
the price is not thirty-one times anything. [ch27](#the-os-layers-cost) measures a real one on real
hardware, and the number is larger than this chapter would lead you to expect — the register saves
are not where the time goes.

**Whether thirty-one is the right number.** It is the *safe* number, and a real kernel saves fewer
by making the convention promise more. Where that is possible and what it buys is a question this
target cannot answer, because the answer is entirely about cost.

**What happens when the caller lies.** Every argument here is a number the handler uses as a
number. The moment an argument is a pointer, the handler is dereferencing an address chosen by
untrusted code, and everything about that is [ch14](#traps-and-system-calls)'s problem —
[ch09](#fork-built-rather-than-read) runs into the first half of it.

## Problems

**7.1 — Add a call, and an error.**
Add a call that can fail for a reason other than being unknown, and return something the caller can
distinguish from a valid result. Say why your choice of sentinel is safe. The test exercises both
the success and the failure and checks the two cannot be confused.

```bash
python3 -m pytest tests/a_system_call_of_your_own/test_problem_1_add_a_call.py
```

**7.2 — Save one register fewer.**
Remove exactly one store and its matching load from the entry stub, and produce a program in which
that omission is visible in the output. The test checks that the register you dropped is the one
your program shows being corrupted.

```bash
python3 -m pytest tests/a_system_call_of_your_own/test_problem_2_one_fewer.py
```

**7.3 — Where does the frame live?**
The stub puts the frame on whatever stack the caller was using. Say what goes wrong if the caller
arrives with a stack pointer it does not own, and change the stub so the kernel uses a stack of its
own instead. The test checks the frame is no longer on the caller's stack.

```bash
python3 -m pytest tests/a_system_call_of_your_own/test_problem_3_whose_stack.py
```

## Where to go next

The unprivileged specification @riscv-isa-unprivileged defines `ecall`; the privileged one @riscv-isa-privileged defines
what it does at each privilege level, which is not the same thing at each.

[ch08](#a-small-integer-that-means-a-device) gives this mechanism its first API worth calling.
