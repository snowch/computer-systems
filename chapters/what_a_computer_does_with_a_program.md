---
title: "What a Computer Does With a Program"
short_title: "ch09 What a Computer Does With a Program"
---

(what-a-computer-does-with-a-program)=
# ch09 · What a Computer Does With a Program

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` and `host` — every example says which |
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **What it measures** | Object and section sizes at each toolchain stage (`xv6`), and instruction counts for the same program under `perf stat` (`host`). |
| **What it captures** | What the compiler emits for the same loop twice: `bench/results/stages-riscv64.json` |
:::

## The question

What actually happens between a source file and a result, and which of it costs anything?

Most of it costs nothing. That is the finding, and it is worth arriving at rather than being
told: a great deal of what looks like work in a C program has been finished before the machine
is switched on, and the part that remains is smaller and stranger than the source suggests.
Separating the two is the skill the rest of Part III is built on, because you cannot ask what a
program costs until you know which parts of it still exist at the time it runs.

## The material

### One command is four programs

`gcc sameanswer.c -o sameanswer` looks like one operation. It is a driver that runs four, each
of which leaves a file on disk that you are allowed to look at and normally never do.

```{figure} _figures/what-a-computer-does-with-a-program-stages.svg
:alt: The four stages of the toolchain, what each hands on, and what each discards.
:width: 100%

Four programs, four handovers. Only one of them makes decisions.
```

The book's walk through them is a shell script rather than a paragraph, because the point is that
you can run it:

```{literalinclude} ../sysfs/tools/stages.sh
:language: bash
:start-at: # 1. Preprocess.
:end-before: for stage in
```

Four commands differing only in where the driver is told to stop. Run it on the program this
chapter uses:

```bash
sysfs/tools/stages.sh sysfs/tools/sameanswer.c /tmp/walk
ls -l /tmp/walk
```

### What each stage is allowed to know

The stages are not equal, and the inequality is the useful part.

**The preprocessor does text substitution and nothing else.** It has never heard of a function, a
type, or a loop. `#include` means *paste that file in here*; a macro means *replace this name with
that text*. When it finishes, every name it introduced is gone and no later stage can tell that a
macro was ever involved. This is why a macro is not a variable and why a bug in one is reported at
a line that does not look wrong.

**The compiler is the only stage that decides anything.** It reads C and writes assembly, and
between those two it is free to do whatever it can prove does not change the result. Everything
this book will later say about optimisation happens here.

**The assembler does a lookup.** Mnemonics become bytes. It knows the addresses of things inside
the file it is reading, and nothing about anything outside it — so where your code refers to
something it cannot see, it writes a hole and a note describing what belongs in it. That note is
a **relocation** @elf-abi.

**The linker fills the holes.** It gathers objects and libraries, decides where everything will
live, and resolves the notes. It is the first stage that knows a real address.

### The same loop, twice

Here is the whole of the program's arithmetic. Two functions, and a reader would be within their
rights to call them the same function:

```{literalinclude} ../sysfs/include/sysfs/stages.h
:language: c
:start-at: #define SYSFS_STAGES_DEFINE_SUMS
:end-before: unsigned long sysfs_sum_folded(void);
```

Same loop, same accumulator, same arithmetic, same optimisation level. The only difference is
where the bound comes from: one is a number the compiler can read, the other arrives in a
register while the program is running.

This is what the compiler did with the first one:

```{include} _generated/what-a-computer-does-with-a-program-folded.md
```

There is no loop. There is no addition. The compiler ran the loop itself, at compile time, and
wrote down what it got — the entire function is a constant and a return. Whatever that sum cost,
it was not paid by the machine that runs this program.

And the second:

```{include} _generated/what-a-computer-does-with-a-program-counted.md
```

That is a loop: a counter, an accumulation, and a branch backwards. It also has a case for zero
and a pair of shifts at the top, which are there because `span` is a 32-bit `unsigned` living in
a 64-bit register and the compiler has to say which half of it means anything —
[ch10](#representing-information)'s subject, arriving early and uninvited, as it tends to.

**Nothing about the source said one of these was expensive.** The difference is entirely about
what the compiler could *prove*. It may replace a loop with its answer only when it can establish
that the loop terminates, that the bound is known, and that the result cannot depend on anything
it cannot see. Take any one of those away and the loop comes back.

That is the first instance of a pattern this book returns to constantly: **the cost of a
construct is not a property of the construct.** It depends on what the compiler was able to
determine about its surroundings, which is why the answer to "is this fast?" is so often "show me
the rest of the file".

### What the object file still owes

Compile the program but do not link it, and it is incomplete in a specific and visible way:

```bash
riscv64-linux-gnu-nm -u /tmp/walk/sameanswer.o
```

`-u` lists undefined symbols — names the object uses and cannot supply. The program calls
`printf`, which lives somewhere else entirely, so the assembler left a hole. After linking there
are none: every name has been resolved to an address, which is most of what "linking" means.

## What we measured

Nothing here is a timing. These are file sizes and symbol counts — facts about what a compiler
produced, which is why they are stamped as artefacts rather than measurements and why CI
regenerates them on every push rather than trusting the committed copy.

What each stage handed to the next:

```{include} _generated/what-a-computer-does-with-a-program-stage-sizes.md
```

Read the two columns against each other, because they disagree in an instructive way.

The preprocessed file is enormous compared with the source, and almost none of it is yours: one
`#include <stdio.h>` drags in every declaration the C library wants you to have. The compiler
then throws nearly all of it away — the assembly it produces is a small fraction of the text it
read — because a declaration you never used generates no code. That collapse is the clearest
possible statement of what a declaration is: a promise about what exists, not an instruction to
build it.

Then the file gets *larger* in bytes while getting much smaller in lines, which is what happens
when text becomes a container format. The object file is ELF: headers, a symbol table,
relocations and a section of instructions, and the instructions are the smallest part.

And then linking:

```{include} _generated/what-a-computer-does-with-a-program-linking.md
```

The last two rows are the same program. One is linked statically against the GNU C library; the
other is linked by xv6 against its own user library, which is a few hundred lines and knows how
to do almost nothing. The difference between them is not your program — your program is
identical — it is the cost of everything `printf` is prepared to do if asked. [ch12](#linking-and-loading) opens
that binary up and says where it all went.

### The same program in both worlds

Build it for each target and run it:

```bash
make xv6-qemu                 # then, at the xv6 prompt: sameanswer
python3 -m pytest tests/test_stages.py -q
```

Both print the same six lines. The folded route and the counted route agree, as they must — they
compute the same sum, and the compiler is not permitted to change the answer, only the work.

What the two targets will not tell you is which route was faster. QEMU has no opinion about time
worth listening to, and the board is not attached to this chapter. [ch20](#the-same-program-on-both-targets) puts that
question properly, and [ch23](#optimising-code) answers it.

## What this cannot tell you

**Nothing here is a cost.** The sizes above are how much space a compiler used, and space is not
time: a smaller binary is not automatically a faster one, and a function that compiles to two
instructions is not automatically cheaper than one that compiles to ten. [ch22](#the-memory-hierarchy) shows a
case where more instructions run faster, for reasons entirely outside the instruction count.

**It is one compiler, at one optimisation level.** Everything in this chapter is what `gcc` at
`-O2` decided, and the conditions line under each table says which `gcc`. A different version may
fold a loop this one leaves alone. That is not a flaw in the example — it is the reason the
listings are regenerated by CI instead of transcribed, and if the compiler changes its mind the
build fails rather than the book quietly becoming wrong.

**"The compiler folded it" is a description, not a mechanism.** This chapter shows you that it
happened and states the conditions under which it is allowed to. It does not show you how the
decision is made, and this book never will — that is a compiler course, and an honest systems
book is better off teaching you to *look at the output* than to model the optimiser.

**One `#include` is not a fair account of the C library.** The preprocessed size above measures
`<stdio.h>` and its dependencies, not "the cost of libc". A program that includes more headers
preprocesses to more text and may still link to the same binary.

**And that size was, briefly, a statement about this machine's directory layout.** The
preprocessor writes into its output the name of every file it pasted in, spelled exactly as the
command line spelled it. So an absolute include path makes the preprocessed file longer on a
machine whose checkout sits deeper, and the same commit measured larger on a CI runner than on a
laptop — the whole difference being the line markers naming one header. Nothing about the number
could have given that away; a size is a size. It surfaced only because CI regenerates this result
instead of trusting the committed copy, and the two disagreed. `stages.sh` now names every path
relative to the repository root, and the runner refuses to stamp a result if any file the walk
produced mentions where the repository lives. Worth knowing in its own right, as the sharpest
possible statement of what stage 1 actually does: it is pasting text, and the paths are part of
the text.

## Problems

Three. Each has a test that passes only when you have solved it, and none of them has an answer
stored anywhere in this repository.

**1.1 — Which stage produced this?**
`tests/what_a_computer_does_with_a_program/problem_1_stages.py` gives you fragments of the four files and asks which program
wrote each one. The fragments are real. The fastest way to solve it is not to stare at them but
to run `sysfs/tools/stages.sh` yourself and look at your own.

```bash
python3 -m pytest tests/what_a_computer_does_with_a_program/test_problem_1_stages.py
```

**1.2 — Predict the ripple.**
Four edits to the program. For each one, say which stages produce a different file afterwards.

This test stores no expected answers. It makes each change, runs the toolchain, and compares the
bytes — so you are not being marked against an answer key, you are being marked against a
compiler. When you disagree with it, it is right, and the interesting question is what you
believed that was not true.

```bash
python3 -m pytest tests/what_a_computer_does_with_a_program/test_problem_2_ripple.py
```

**1.3 — Take the folding away.**
Write a function that computes the same sum and that the compiler *cannot* evaluate for you. It
must still contain a loop, and the machine must actually run it — the test disassembles what came
out and looks for a backward branch, so returning a constant will not pass and neither will a
loop the optimiser can see through.

```bash
python3 -m pytest tests/what_a_computer_does_with_a_program/test_problem_3_unfold.py
```

There is more than one way to do it and they are not equally good. The section on the same loop
twice says what the compiler has to be able to prove; take away whichever of those you like.

## Where to go next

The ELF specification @elf-abi defines the object format the assembler writes and the linker
reads: sections, symbols and relocations, all of which [ch12](#linking-and-loading) takes apart properly. It is
worth skimming now purely to see that the thing `nm` printed is a documented structure rather
than a convention.

The RISC-V psABI @riscv-psabi says which relocation types exist and what each one means, and is
the document that explains why a call to `printf` looks the way it does in the object file.

[ch10](#representing-information) goes back to the thing the compiler was manipulating in the first place: what a
number is to this machine, and when that answer bites.
