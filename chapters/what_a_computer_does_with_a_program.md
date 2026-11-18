---
title: "12 · What a Computer Does With a Program"
short_title: "12 · What a Computer Does With a Program"
---

(what-a-computer-does-with-a-program)=
# 12 · What a Computer Does With a Program

:::{note} Before you start
:class: chapter-header

| | |
|---|---|
| **Target** | `xv6` and `host` — every example says which |
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **Evidence** | Files and symbols produced as the toolchain turns source into a program. |
| **What it captures** | What the compiler emits for the same loop twice: `bench/results/stages-riscv64.json` |
:::

## The question

What actually happens between a source file and a result, and which of it costs anything?

Most of it costs nothing. A great deal of what looks like work in a C program has been finished
before the machine is switched on, and the part that remains is smaller and stranger than the
source suggests. Separating the two is the skill the rest of [Part III](#part3) is built on,
because you cannot ask what a program costs until you know which parts of it still exist at the
time it runs.

(what-a-computer-does-with-a-program-example)=
## Keep and inspect the toolchain outputs

### One command is four programs

`gcc sameanswer.c -o sameanswer` looks like one operation. `gcc` is a launcher that runs four
programs in turn, each of which leaves a file on disk that you are allowed to look at and
normally never do.

```{figure} _figures/what-a-computer-does-with-a-program-stages.svg
:alt: The four stages of the toolchain, what each hands on, and what each discards.
:width: 100%

Four programs, four handovers. Only one of them makes decisions.
```

Here is the walk through them, as a shell script rather than a paragraph, so you can run it
yourself:

```{literalinclude} ../sysfs/tools/stages.sh
:language: bash
:start-at: # 1. Preprocess.
:end-before: for stage in
```

The script uses the Linux RISC-V GCC toolchain and retains the intermediate files. From your
repository root, run it on the original program. Use a new temporary directory for this run:

```bash
walk_dir=$(mktemp -d)
sysfs/tools/stages.sh sysfs/tools/sameanswer.c "$walk_dir"
ls -l "$walk_dir"
```

Read the `stage` lines for the stage name, file size in bytes and newline count. Match
`sameanswer.i`, `sameanswer.s`, `sameanswer.o` and `sameanswer` to those stages. The first two
are text files. The last two are ELF binary files.

### What each stage is allowed to know

The stages differ in what each one is allowed to know, and that difference explains most of what
each one does.

**The preprocessor does text substitution and nothing else.** It has never heard of a function, a
type, or a loop. `#include` means *paste that file in here*; a macro means *replace this name with
that text*. What comes out — one source file with everything it included pasted in — is what the
compiler actually sees, and is called a *translation unit*. When the preprocessor finishes, every
name it introduced is gone and no later stage can tell that a macro was ever involved. This is why a macro is not a variable and why a bug in one is reported at
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

Here is the whole of the program's arithmetic. Two functions, close enough that you could
reasonably call them the same function:

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
a 64-bit register and the compiler has to say which half of it means anything. That is
[ch13](#representing-information)'s subject, arriving early.

**Nothing about the source said one of these was expensive.** The difference is entirely about
what the compiler could *prove*. It may replace a loop with its answer only when it can establish
that the loop terminates, that the bound is known, and that the result cannot depend on anything
it cannot see. Take any one of those away and the loop comes back.

This book returns to that pattern constantly: **the cost of a construct is not a property of the
construct.** It depends on what the compiler was able to determine about its surroundings, which
is why the answer to "is this fast?" is so often "show me the rest of the file".

### What the object file still owes

Compile the program but do not link it, and it is incomplete in a specific and visible way:

```bash
riscv64-linux-gnu-nm -u "$walk_dir/sameanswer.o"
```

`-u` lists undefined symbols — names the object uses and cannot supply. The output marks each undefined symbol with `U`. Names such as `__printf_chk` or `puts` can
appear when this compiler translates a source-level `printf` call. Check the script's
`undefined_in_object` and `undefined_in_program` lines to see whether the static linker
resolved those references.

## What we measured

Nothing here is a timing. These are file sizes and symbol counts — facts about what a compiler
produced, which is why they are stamped as artefacts rather than measurements and why CI
regenerates them on every push rather than trusting the committed copy.

What each stage handed to the next:

```{include} _generated/what-a-computer-does-with-a-program-stage-sizes.md
```

Read the two columns against each other, because bytes and lines do not move together.

The preprocessed file is enormous compared with the source, and almost none of it is yours: one
`#include <stdio.h>` drags in every declaration the C library wants you to have. The compiler
then throws nearly all of it away — the assembly it produces is a small fraction of the text it
read — because a declaration you never used generates no code. That collapse shows what a
declaration is: a promise about what exists, not an instruction to build it.

Then the file gets *larger* in bytes while getting much smaller in lines, which is what happens
when text becomes a container format. The object file is ELF: headers, a symbol table,
relocations and a section of instructions, and the instructions are the smallest part.

And then linking:

```{include} _generated/what-a-computer-does-with-a-program-linking.md
```

The two linked sizes are the same program. One is linked statically — every library routine it
needs copied into the file — against the GNU C library; the other is linked by xv6 against its
own user library, which is a few hundred lines and knows how to do almost nothing. The
difference between them is not your program — your program is identical — it is the cost of
everything `printf` is prepared to do if asked. [ch15](#linking-and-loading) opens that binary
up and says where it all went.

### The same program in both worlds

From your repository root, run both original versions. The first uses your local C compiler.
The second builds and boots xv6 and types `sameanswer` at its shell.

```bash
./run sameanswer --target host
./run sameanswer --target xv6
```

For each run, compare `folded` and `counted`, then read `agree`. Do both routes return the
same sum on each environment? These are arithmetic results. [ch23](#the-same-program-on-both-targets)
compares execution time on native hardware for a separate program.

## What this cannot tell you

**Nothing here is a cost.** The sizes above are how much space a compiler used, and space is not
time: a smaller binary is not automatically a faster one, and a function that compiles to two
instructions is not automatically cheaper than one that compiles to ten. [ch27](#the-cpu) shows a
case where more instructions run faster, for reasons entirely outside the instruction count.

**It is one compiler, at one optimisation level.** Everything in this chapter is what `gcc` at
`-O2` decided, and the conditions line under each table says which `gcc`. A different version may
fold a loop this one leaves alone. That is why the listings are regenerated by CI instead of
transcribed: if the compiler changes its mind the build fails, rather than the book quietly
becoming wrong.

**"The compiler folded it" is a description, not a mechanism.** This chapter shows you that it
happened and states the conditions under which it is allowed to. It does not show you how the
decision is made, and this book never will — that is a compiler course, and an honest systems
book is better off teaching you to *look at the output* than to model the optimiser.

**One `#include` is not a fair account of the C library.** The preprocessed size above measures
`<stdio.h>` and its dependencies, not "the cost of libc". A program that includes more headers
preprocesses to more text and may still link to the same binary.

**And that size briefly depended on where the repository sat on disk.** The preprocessor writes
into its output the name of every file it pasted in, spelled exactly as the command line spelled
it. So an absolute include path makes the preprocessed file longer on a machine whose checkout
sits deeper, and the same commit measured larger on a CI runner than on a laptop — the whole
difference being the lines the preprocessor writes to say which file each piece came from, naming
one header. Nothing about the number could have given that away; a size is a size. It surfaced
only because CI regenerates this result
instead of trusting the committed copy, and the two disagreed. `stages.sh` now names every path
relative to the repository root, and the runner refuses to stamp a result if any file the walk
produced mentions where the repository lives. It shows exactly what stage 1 does: it pastes text,
and the paths are part of the text.

## Problems

Use the files below in your local checkout. Run each test command from the repository root.

**12.1 — Which stage produced this?**
Open `tests/what_a_computer_does_with_a_program/problem_1_stages.py`. Complete
`which_stage_wrote_this`. Use the stage command above and compare its generated files with the
fragments in the test.

```bash
python3 -m pytest tests/what_a_computer_does_with_a_program/test_problem_1_stages.py
```

**12.2 — Predict the ripple.**
Open `tests/what_a_computer_does_with_a_program/problem_2_ripple.py`. Complete
`stages_disturbed_by`. For each proposed edit, predict which stages will produce different
files. The test applies the edits to temporary files and reports which predictions differ from
the compiler output.

```bash
python3 -m pytest tests/what_a_computer_does_with_a_program/test_problem_2_ripple.py
```

**12.3 — Take the folding away.**
Open `tests/what_a_computer_does_with_a_program/problem_3_unfold.py`. Edit the C function in
`UNFOLDABLE_SUM`. It should sum the integers below `span` and keep a loop in the compiled
result. The test checks the returned sum and looks for a backward branch.

```bash
python3 -m pytest tests/what_a_computer_does_with_a_program/test_problem_3_unfold.py
```

## Where to go next

The ELF specification @elf-abi defines the object format the assembler writes and the linker
reads: sections, symbols and relocations, all of which [ch15](#linking-and-loading) takes apart properly. It is
worth skimming now purely to see that the thing `nm` printed is a documented structure rather
than a convention.

The RISC-V psABI @riscv-psabi says which relocation types exist and what each one means, and is
the document that explains why a call to `printf` looks the way it does in the object file.

[ch13](#representing-information) goes back to the thing the compiler was manipulating in the first place: what a
number is to this machine, and when that answer bites.
