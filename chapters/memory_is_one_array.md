---
title: "03 · Memory Is One Array"
short_title: "03 · Memory Is One Array"
---

(memory-is-one-array)=
# 03 · Memory Is One Array

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `xv6` for the kernel context. Your computer’s C compiler for the first run, and RISC-V for the recorded instruction listings. |
| **Prerequisites** | A local checkout from [ch00](#prerequisites-and-setup) and a C compiler available as `cc`. |
| **Evidence** | Printed values and byte distances, then RISC-V instructions for pointer and member access. |
:::

## The question

What can a C declaration tell you about the size, location and lifetime of a value?

Start with a complete program. Use its output to distinguish the value a pointer reaches from
the byte distance between array elements. Then look for that distance in the compiler's
instructions.

(memory-is-one-array-example)=
## Trace values and addresses in C

(one-whole-program)=
### Run your first C program

The checkout contains `sysfs/tools/firstc.c`. The listing below shows that file. Run the
original from your local checkout before you edit it.

```{literalinclude} ../sysfs/tools/firstc.c
:language: c
```

The `#include` lines bring in declarations for `printf` and the integer types. Execution
starts in `main`. The `printf` calls write values to the terminal, and `return 0` reports
successful completion to the shell.

From your repository root, run:

```bash
./run firstc
```

`./run` builds and runs the program with your local `cc`. In the terminal, compare `value`
with `roundtrip`. Then compare the byte distances on the `step int32` and `step int64` lines.
Which numbers describe stored values, and which describe the distance between elements?

The table is a saved correctness run of the original program. Its conditions identify an
AArch64 cross-build executed using user-mode QEMU.

```{include} _generated/memory-is-one-array-firstc.md
```

Now open `sysfs/tools/firstc.c` in your text editor. Change `int value = 42;` to
`int value = 17;` and run `./run firstc` again. Check whether `value` and `roundtrip` both
become 17. Do the `step int32` and `step int64` fields change with them?

(memory-is-one-array-and-everything-has-an-index)=
### Model memory as numbered bytes

Picture the address space available to the program as numbered bytes. In this model, a C
object occupies a region and its address identifies where the region starts. The model helps you
reason about sizes and offsets. The C rules determine which objects a pointer may access and
how far it may move within an array.

For any declaration, ask where the object lives, how long it stays there and how large it is.
For this example, the address of a value identifies its first byte. Later, [ch17](#virtual-memory)
shows how the processor translates a program's addresses to physical memory.

### `&` and `*`, watched rather than described

`&x` gives the address of `x`. A *pointer* is a value that can refer to an object or function.
When `p` points to an object, `*p` designates that object. In the `printf` call, evaluating
`*where` reads the object originally named `value`. That is why the printed values agree.

The program prints relative distances. The addresses of the arrays can vary between runs.
The distance between consecutive elements of an array follows the element type. In the recorded
run the two distances differ even though both arrays contain the same number of elements.

(a-pointer-is-an-index-with-a-type-stapled-to-it)=
### The pointer's type determines the step

`int *p` declares a pointer to an `int`. When it points into an array of integers, `p + 1`
advances by one element. The type tells the compiler how many bytes that step spans.

Two functions, each taking a pointer and returning the element after the one it points at. The
source of each is the same three characters, `p + 1`.

```{literalinclude} ../sysfs/lib/declarations.c
:language: c
:start-at: int32_t sysfs_step_narrow
:end-before: int64_t sysfs_reach_through
```

If `4(a0)` and the address column are unfamiliar, [ch02](#reading-a-listing) is the key for
reading these. What is needed here is one line of it: parentheses mean memory, and the number in
front is a byte offset, so `4(a0)` is the memory four bytes past the address in `a0`. Watch that
number.

The narrow one:

```{include} _generated/memory-is-one-array-step-narrow.md
```

The wide one:

```{include} _generated/memory-is-one-array-step-wide.md
```

One load each, and they are not the same load. The narrow one loads a word from four bytes along;
the wide one loads a doubleword from eight. (The `ret` after it is the function returning, which is
why each listing is two instructions rather than one.) **`+ 1` never means "one byte".** It means
one *element*, and the element size comes from the type, and the type is not in the expression you
are reading.

This is why a pointer's type matters even when you never dereference it — never apply `*` to
it — and it is why a cast to a different pointer type changes what arithmetic on it does. Nothing
about `p + 1` on the page tells you the answer; you have to know what `p` was declared as.

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
puzzle for its own sake: `int (*f)(void)` is how every device driver in [ch19](#interrupts-and-drivers) is reached,
and `const int *` against `int *const` is a distinction the kernel relies on constantly to say
which of two things it promises not to change.

Problem 3.1 is this table, generated rather than reproduced, with declarations you have not seen.

### Arrays, and why a pointer cannot carry a length

An array is a run of elements, and its name in most expressions turns into the index of its first
one. Pass an array to a function and what arrives is a pointer — the length does not travel with
it, and cannot, because there is nowhere in a pointer to put it.

That is why every kernel function that takes a buffer also takes a count. It is not a style
preference; there is no alternative. [ch05](#c-for-people-who-will-read-a-kernel) shows the compiler discarding a length written
into a parameter's brackets, and [ch13](#representing-information) has the bug it causes.

A string in C is this with one extra convention: a run of bytes ending in a zero byte. The zero is
the length, stored at the end instead of the beginning, which makes finding the length a loop
rather than a lookup and makes forgetting to write it a bug that reads off the end of the array.

### Structs, and what `->` really is

A struct is several objects at fixed offsets from one address. `record->third` means: take the
index in `record`, add the offset of `third`, and read what is there.

```{literalinclude} ../sysfs/lib/declarations.c
:language: c
:start-at: int64_t sysfs_reach_through
```

```{include} _generated/memory-is-one-array-reach.md
```

Two loads and an add. **There is no member lookup.** The names `second` and `third` do not exist by
the time the machine sees this; they became the numbers in those two load instructions, decided
when the file was compiled. `a->b` is exactly `(*a).b`, and both are exactly "an offset on a
load".

Which offsets, and why they are not simply the sum of the sizes before them, is [ch13](#representing-information)'s
subject. What matters here is that the offsets are fixed at compile time and the name is gone.

### Casts, and the two kinds of arithmetic

A cast says "treat these bytes as this type instead". Between pointer types it changes nothing
about the bytes and everything about what arithmetic on them means, because the type is what sets
the step size.

A kernel casts constantly between a pointer and a plain integer, because an address genuinely *is*
a number there — a physical page is a number, a device register is a number — and the two kinds of
arithmetic are different:

- **Pointer arithmetic** scales by the element. `p + 1` moves by `sizeof(*p)`, the size in
  bytes of what `p` points at.
- **Address arithmetic** does not. `(uint64)p + 1` moves by one byte.

Rounding an address to a page boundary is address arithmetic, which is why the kernel's rounding
macros cast to an integer type first and back afterwards. Problem 3.3 is writing the pair, and the
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
list, tree and queue in the kernel is built from, and [ch04](#c-without-a-runtime) shows the free list xv6 makes
out of the free memory itself.

## What we measured

Nothing here is a cost. Two things, and they are the same fact seen from two sides.

First, what the program printed — the chapter's claims in a form you can reproduce: that `*&x` is
`x`, and that consecutive elements are one element apart rather than one byte. The runner refuses
to stamp a run where either stops holding, because the chapter asks the reader to take both on
trust for exactly as long as it takes to run the program.

Then three listings, captured by the machinery [ch12](#what-a-computer-does-with-a-program) explains and re-captured by CI on
every push, showing the same two facts from underneath: that `p + 1` compiles to a different
offset for different element types, and that `->` compiles to an offset on a load with no lookup
of any kind.

Both are facts about what this compiler did. That they are *required* is a claim about the
standard @iso-c17 and would hold on a compiler emitting entirely different instructions.

## What this cannot tell you

**How to program.** Deliberately. Control flow, functions, operators and the shape of a program
are assumed from whatever language you already use, and C spells them much as it does. What is not
assumed is the memory model, because that is the part your other language was built to hide.

**What any of this costs.** No chapter in this part has a clock in it. [ch25](#the-memory-hierarchy) is where
following a pointer acquires a price, and the price turns out to depend on something no listing
here can show.

**Why the struct offsets are what they are.** This chapter shows that `->` becomes an offset. It
does not say how the offsets were chosen, and the answer is not "add up the sizes" —
[ch13](#representing-information) takes it apart.

**Whether a pointer is safe to use.** C's rules require a live object of a suitable type for
these accesses. A numerically plausible address can still violate those rules. The processor's
page checks, described in [ch18](#page-faults-as-a-feature), enforce which memory is mapped and
accessible at page granularity.

## Problems

Edit `tests/memory_is_one_array/declarations.c` in your checkout. Run each test command from
the repository root.

**3.1 — Say what each declaration names.**
Complete `d_classify`. Use the declaration to tell what each name denotes. For declarations
that differ only in parentheses, identify what the parentheses make the pointer refer to.

```bash
python3 -m pytest tests/memory_is_one_array/test_problem_1_declarations.py
```

**3.2 — Walk a buffer without an index.**
Complete `d_length`, `d_copy` and `d_compare`. Move pointers through the buffer without using
a subscript. The test checks the returned length, copied bytes and comparison result.

```bash
python3 -m pytest tests/memory_is_one_array/test_problem_2_walking.py
```

**3.3 — Round an address both ways.**
Complete `d_round_down` and `d_round_up`. Round an integer address to the adjacent boundaries
for the given power-of-two alignment. Check both reported addresses for any failing input.

```bash
python3 -m pytest tests/memory_is_one_array/test_problem_3_rounding.py
```

## Where to go next

The C standard @iso-c17 is the authority on the claims here that are about the language rather
than about a compiler — §6.5.6 on what adding an integer to a pointer means, and §6.7.6 on how a
declaration is assembled from the inside out.

[ch04](#c-without-a-runtime) is next, and it is the chapter for a reader who already writes C.
Every assumption an application programmer is entitled to make — that allocation succeeds, that the
library is there, that memory is memory, that one thread is looking — stops holding, and the
chapter counts what is missing rather than asserting it.
