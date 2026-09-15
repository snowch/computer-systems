---
title: "Linking and Loading"
short_title: "13 · Linking and Loading"
---

(linking-and-loading)=
# 13 · Linking and Loading

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch12](#machine-level-code-on-riscv) |
| **What it measures** | Sections, segments and symbol counts for xv6's own binaries, read by this book's reader: `bench/results/elf-xv6.json` |
:::

## The question

How does a file on disk become an address space?

[ch10](#what-a-computer-does-with-a-program) left the linker as the stage that "fills in the holes" and moved on. This chapter
opens the file it produced. By the end you should be able to say what is in an executable, which
parts of it will exist at run time and which will not, and what `exec` has to do to turn one into
a running program — and you should have written enough of a reader to believe it.

## The material

### Write the reader

A reader who has only ever used `readelf` believes an ELF file is a thing a tool understands. The
fastest cure is to write a tool.

```{literalinclude} ../sysfs/tools/elfdump.c
:language: c
:start-at: /* Field offsets, straight out of the specification.
:end-before: #define PH_TYPE
```

Build it and run it here:

```bash
./run elfdump
```

That is most of what an ELF file is: a header with a magic number, a handful of sizes, and the
offsets of two arrays. Everything else is found by following one of those offsets. There is no
`#include <elf.h>` anywhere in `sysfs/tools/elfdump.c`, deliberately — the structures are declared
from the specification @elf-abi, because half the point is that they are a documented layout of
bytes rather than something only a library may know.

```bash
cc -O2 -o elfdump sysfs/tools/elfdump.c
./elfdump xv6/stage/user/_sameanswer
```

### Two arrays, two audiences

The two arrays describe the same bytes to different readers, and confusing them is the single
most common muddle about executables.

**Sections** are the linker's view. They are named, they are numerous, and most of them exist to
be combined with the corresponding sections of other objects: put all the `.text` together, all
the `.rodata` together, resolve what refers to what. After linking, most of them have no further
purpose — the debug sections in particular are enormous and are never loaded.

**Segments** are the loader's view, and there are far fewer:

```{figure} _figures/linking-and-loading-segments.svg
:alt: Eighteen ELF sections collapsing into two loadable segments.
:width: 100%

The same bytes, described twice. The second description is the one the machine acts on.
```

A segment says: *take this many bytes from this offset in the file, put them at this address, give
them these permissions.* That is nearly the whole interface between a file and an address space.

```{include} _generated/linking-and-loading-shape.md
```

Eighteen sections, two segments. The collapse is by permission: everything that needs to be
readable and executable goes in one, everything writable in the other. Permissions are a property
of a *page*, not of a symbol, which is why the grouping is by what the hardware can enforce rather
than by what the programmer named.

### The segment that is partly not in the file

```{include} _generated/linking-and-loading-segment-table.md
```

Look at the last two columns of the writable rows. Those segments occupy bytes in memory and none
at all in the file.

That is `.bss`: variables that start as zero. Storing them would mean putting a run of zeroes in
every binary, so the format does not. It records how much space to provide and the loader provides
it, already zeroed. A global array of a million integers costs a number in a header.

Two consequences worth carrying forward. A binary's size on disk tells you little about its size in
memory — [ch10](#what-a-computer-does-with-a-program)'s comparison of glibc against xv6's library was about code, and this is the
other direction. And "zero-initialised" is not a favour the language does you at some cost; it is
the *cheapest* initial state, because it is the one the loader was going to produce anyway.

### What `exec` actually does

The interface above is small enough that you can now read the kernel side of it. xv6's `exec`
opens the file, checks the magic number, walks the program headers, and for each loadable one
allocates pages and copies bytes in @xv6-riscv-source. Then it builds a stack, puts the arguments
on it, and switches the process to the new address space.

Everything it does is a consequence of what the file said. It has no idea what the program does,
what language it was written in, or what its functions are called — the symbol table is not
consulted. **An ELF executable is a set of instructions to a loader, and the code is incidental.**

The permissions matter here in a way they do not in a file. The code segment is mapped
executable-and-not-writable and the data segment writable-and-not-executable, and those two
prohibitions are enforced by the page table rather than by convention. [ch15](#virtual-memory) is where that
enforcement becomes a mechanism you can see and [ch16](#page-faults-as-a-feature) is where breaking it becomes a fault
you can catch.

### What is left over

The symbol table is not loaded and is not needed to run the program. It survives in the file for
the benefit of debuggers and of anybody reading it, which is why stripping a binary makes it
smaller without making it slower, and why a stripped binary produces a backtrace full of addresses
and no names.

That is worth knowing in both directions: the names in a backtrace are a convenience the file
happens to carry, and a production binary that has been stripped has thrown them away
permanently — which is why [ch28](#whole-machine-profiling) spends time on keeping symbols around for the profiler.

## What we measured

Sections, segments and symbol counts for two xv6 programs, read by `sysfs/tools/elfdump.c` rather
than by `readelf`. Facts about files, stamped as artefacts, regenerated by CI.

xv6's binaries were chosen over Linux ones for a reason worth stating: a Linux executable's answer
to "where does this get loaded" is complicated by a dynamic loader and a position-independent
layout, both of which deserve their own explanation and neither of which is the mechanism
underneath. xv6 links a program to a fixed address and puts it there. That is the simple version
of what the complicated version is doing.

## What this cannot tell you

**How dynamic linking works.** Every binary here is statically linked to a fixed address. Shared
libraries, relocation at load time, the procedure linkage table and the global offset table are
all absent, and they are the majority of what happens when you run a program on Linux.
[ch27](#the-os-layers-cost) touches the cost of the machinery; this chapter does not describe it.

**What a linker script decides.** xv6 has one, it fixes the addresses in the table above, and this
chapter shows the *result* of it rather than the language it is written in. Linker scripts are a
small, strange, badly documented language, and the honest thing is to say that the addresses came
from somewhere and point at the file.

**Anything about time.** Loading a program costs something — pages have to be allocated and bytes
copied — and this chapter has no way to measure it. [ch27](#the-os-layers-cost) measures what a process costs to
start on a machine with a clock.

**Whether the symbol table is "wasted space".** It is not loaded, so it costs no memory at run
time; it costs file size and it buys every debugging session you will ever have. That is a
trade-off rather than a defect, and which side of it you want depends on things this chapter has
no opinion about.

## Problems

Three, and the first is the one that makes the format stop being magic.

**13.1 — Finish the reader.**
Two functions `sysfs/tools/elfdump.c` does not contain: how much memory a program occupies once
loaded, and which section covers a given address. The second one requires the indirection this
chapter describes — a section header does not hold its own name.

The expected answers are not stored. The test runs the book's finished reader on the same binary
and compares, so the target moves with the file rather than going stale the next time xv6 is
rebuilt.

```bash
python3 -m pytest tests/linking_and_loading/test_problem_1_reader.py
```

**13.2 — Which of these links?**
Five pairs of translation units. Predict whether each produces a program. The test actually links
them.

One of the five links successfully and produces a program that is wrong, which is not a trick: it
is the reason the C language has a reputation. Say whether it links; the chapter has already told
you what to think about the fact that it does.

```bash
python3 -m pytest tests/linking_and_loading/test_problem_2_resolve.py
```

**13.3 — Read the error, name the cause.**
Four link failures, with the messages a linker really produced during the test run. Name the cause
of each.

Linker errors are terse, they name symbols rather than files, and they come from a program that
knows nothing about your intentions. Reading one is a skill, and it is the difference between
twenty minutes and ten seconds.

```bash
python3 -m pytest tests/linking_and_loading/test_problem_3_diagnose.py
```

## Where to go next

The ELF specification @elf-abi is the document `sysfs/tools/elfdump.c` was written from, and it is
unusually pleasant for a format specification: the structures are small, the field names are the
ones every tool uses, and you can check the reader against it line by line.

The RISC-V psABI @riscv-psabi supplies the architecture-specific half — which relocation types
exist and what each computes — and is where to look when a relocation name appears in an error
message.

xv6's `kernel/exec.c` @xv6-riscv-source is about a hundred and fifty lines and is now readable end
to end. It is the shortest complete answer to "what happens when you run a program" that exists
anywhere, and having written a reader for the format it consumes, you will find it contains no
surprises at all. That feeling is what [Part III](#part3) was for.

[ch14](#traps-and-system-calls) begins [Part IV](#part4) by asking what happens when that program asks the kernel for
something.
