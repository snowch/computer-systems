---
title: "Reading C"
short_title: "ch01 Reading C"
---

(ch01)=
# ch01 · Reading C

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch00](#ch00) |
| **What it measures** | What `p + 1` and `->` become: `bench/results/declarations-riscv64.json` |
:::

## The question

How do I read a C declaration, and what does each piece of it become?

:::{note} Which of these three chapters you need
:class: dropdown

**If you already write C**, skip to [ch02](#ch02). This chapter is the on-ramp; ch02 is the one
about the habits that stop working in a kernel, and it is written for you.

**If you program fluently in something else and have never written C**, start here. You are not
being taught to program — loops, conditionals, functions and operators are assumed, and C spells
them much as your language does. You are being taught C's *model*, which is the part that is
genuinely different and the part a kernel is made of.
:::

## The material

### Memory is one array, and everything has an index

Your other language has objects that hold values, and a runtime that knows where they are. C has
one array of bytes, numbered from zero, and every object is some run of it. That is not a
simplification for teaching. It is the whole model, and every difficulty later is a difficulty
about it.

Three questions follow, and they are the ones worth asking of any C you read:

- **Where does this live?** In the current call's region, in one that lasts the whole run, or in
  memory somebody asked for.
- **How long does it stay there?** Until the function returns, for ever, or until somebody says
  otherwise.
- **How big is it?** Which is a question about its *type*, and the reason types exist at all.

`&x` gives you the index of `x`'s first byte. `*p` goes to the index in `p` and reads what is
there. Those two are inverses and there is nothing else to them.

### A pointer is an index with a type stapled to it

`int *p` says: `p` holds an index, and what lives at that index is an `int`. The type is not
decoration. It is how the compiler knows how many bytes to take, how to interpret them, and — this
is the part that surprises people — **how far one step is**.

Here are two functions. Both take a pointer and return the element after the one it points at.
The source of each is the same three characters, `p + 1`.

```{literalinclude} ../sysfs/lib/declarations.c
:language: c
:start-at: int32_t sysfs_step_narrow
:end-before: int64_t sysfs_reach_through
```

The narrow one:

```{include} _generated/ch01-step-narrow.md
```

The wide one:

```{include} _generated/ch01-step-wide.md
```

One instruction each, and they are not the same instruction. The narrow one loads a word from four
bytes along; the wide one loads a doubleword from eight. **`+ 1` never means "one byte".** It means
one *element*, and the element size comes from the type, and the type is not in the expression you
are reading.

This is why a pointer's type matters even when you never dereference it, and it is why a cast to a
different pointer type changes what arithmetic on it does. Nothing about `p + 1` on the page tells
you the answer; you have to know what `p` was declared as.

### Reading a declaration

C declarations are famously hard to read and the reason is that they are written to *mirror use*.
`int *p` is not "p is a pointer to int" written awkwardly. It is "the expression `*p` has type
`int`" — the declaration shows you the shape of the thing that finally yields an `int`.

Once you know that, the rule is mechanical: **start at the name, and read outwards, taking
whatever binds tightest first.** `[]` and `()` bind tighter than `*`, and parentheses override.

| Declaration | Read it as |
|---|---|
| `int *p` | `p` is a pointer to `int` |
| `int p[4]` | `p` is an array of four `int` |
| `int *p[4]` | `p` is an array of four pointers to `int` |
| `int (*p)[4]` | `p` is a pointer to an array of four `int` |
| `int *f(void)` | `f` is a function returning a pointer to `int` |
| `int (*f)(void)` | `f` is a pointer to a function returning `int` |
| `const int *p` | `p` points at an `int` you may not write through |
| `int *const p` | `p` is a pointer you may not repoint |

The two pairs that differ only by parentheses are the ones worth doing slowly, and they are not a
puzzle for its own sake: `int (*f)(void)` is how every device driver in [ch11](#ch11) is reached,
and `const int *` against `int *const` is a distinction the kernel relies on constantly to say
which of two things it promises not to change.

Problem 1.1 is this table, generated rather than reproduced, with declarations you have not seen.

### Arrays, and the promise that decays

An array is a run of elements, and its name in most expressions turns into the index of its first
one. Pass an array to a function and what arrives is a pointer — the length does not travel with
it, and cannot, because there is nowhere in a pointer to put it.

That is why every kernel function that takes a buffer also takes a count. It is not a style
preference; there is no alternative. [ch03](#ch03) shows the compiler discarding a length written
into a parameter's brackets, and [ch05](#ch05) has the bug it causes.

A string in C is this with one extra convention: a run of bytes ending in a zero one. The zero is
the length, stored at the end instead of the beginning, which makes finding the length a loop
rather than a lookup and makes forgetting to write it a bug that reads off the end of the array.

### Structs, and what `->` really is

A struct is several objects at fixed offsets from one address. `record->third` means: take the
index in `record`, add the offset of `third`, and read what is there.

```{literalinclude} ../sysfs/lib/declarations.c
:language: c
:start-at: int64_t sysfs_reach_through
```

```{include} _generated/ch01-reach.md
```

Two loads and an add. **There is no member lookup.** The names `second` and `third` do not exist by
the time the machine sees this; they became the numbers in those two load instructions, decided
when the file was compiled. `a->b` is exactly `(*a).b`, and both are exactly "an offset on a
load".

Which offsets, and why they are not simply the sum of the sizes before them, is [ch05](#ch05)'s
subject. What matters here is that the offsets are fixed at compile time and the name is gone.

### Casts, and the two kinds of arithmetic

A cast says "treat these bytes as this type instead". Between pointer types it changes nothing
about the bytes and everything about what arithmetic on them means, for the reason two sections
back.

A kernel casts constantly between a pointer and a plain integer, because an address genuinely *is*
a number there — a physical page is a number, a device register is a number — and the two kinds of
arithmetic are different:

- **Pointer arithmetic** scales by the element. `p + 1` moves by `sizeof(*p)`.
- **Address arithmetic** does not. `(uint64)p + 1` moves by one byte.

Rounding an address to a page boundary is address arithmetic, which is why the kernel's rounding
macros cast to an integer type first and back afterwards. Problem 1.3 is writing the pair, and the
thing to get right is that rounding *up* and rounding *down* are not the same expression with a
different sign.

### A structure that points at its own kind

The last construct, and the one that makes the next chapter possible.

```c
struct node {
  int value;
  struct node *next;
};
```

A struct cannot contain itself — it would have no size — but it can contain the *index* of another
one, because an index has a size regardless of what it points at. That single fact is what every
list, tree and queue in the kernel is built from, and [ch02](#ch02) shows the free list xv6 makes
out of the free memory itself.

## What we measured

Nothing here is a cost. Three listings, captured by the machinery [ch04](#ch04) explains and
re-captured by CI on every push, establishing two things a reader would otherwise have to take on
trust: that `p + 1` compiles to a different offset for different element types, and that `->`
compiles to an offset on a load with no lookup of any kind.

Both are facts about what this compiler did. That they are *required* is a claim about the
standard @iso-c17 and would hold on a compiler emitting entirely different instructions.

## What this cannot tell you

**How to program.** Deliberately. Control flow, functions, operators and the shape of a program
are assumed from whatever language you already use, and C spells them much as it does. What is not
assumed is the memory model, because that is the part your other language was built to hide.

**What any of this costs.** No chapter in this part has a clock in it. [ch17](#ch17) is where
following a pointer acquires a price, and the price turns out to depend on something no listing
here can show.

**Why the struct offsets are what they are.** This chapter shows that `->` becomes an offset. It
does not say how the offsets were chosen, and the answer is not "add up the sizes" —
[ch05](#ch05) takes it apart.

**Whether your pointer is valid.** C has no answer to this and neither does the hardware, until
[ch10](#ch10). A pointer is an index; nothing checks that the index means anything.

## Problems

Three, in `tests/ch01/declarations.c`.

**1.1 — Say what each declaration names.**
The test generates declarations and asks you to classify them. The two that differ only by
parentheses are the point of the exercise, and they are the two you will meet again in
[ch11](#ch11).

```bash
python3 -m pytest tests/ch01/test_problem_1_declarations.py
```

**1.2 — Walk a buffer without an index.**
Reimplement three of the routines the kernel supplies for itself, using pointers that move rather
than a subscript. The versions in `kernel/string.c` are written this way, and this is so you can
read them.

```bash
python3 -m pytest tests/ch01/test_problem_2_walking.py
```

**1.3 — Round an address both ways.**
Given an address and a power-of-two alignment, round up and round down. Address arithmetic, not
pointer arithmetic, and the kernel does this on every page it touches.

```bash
python3 -m pytest tests/ch01/test_problem_3_rounding.py
```

## Where to go next

The C standard @iso-c17 is the authority on the claims here that are about the language rather
than about a compiler — §6.5.6 on what adding an integer to a pointer means, and §6.7.6 on how a
declaration is assembled from the inside out.

[ch02](#ch02) is the other half of this part, and the half for a reader who already writes C. Every
assumption an application programmer is entitled to make — that allocation succeeds, that the
library is there, that memory is memory, that one thread is looking — stops holding, and the
chapter counts what is missing rather than asserting it.
