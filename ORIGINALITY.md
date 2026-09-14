# Originality

This book covers ground that well-known textbooks also cover. It is entirely original work, and
this file is the record of how that was kept true.

**One entry per chapter, added in the same commit as the chapter.** Each names the works closest
to it in *subject* — the ones a reader might reasonably ask "isn't this just…?" about — and states
in one line how this chapter's structure, examples and figures differ. `tests/test_book.py` fails
a chapter that has lost its `[DRAFT]` marker without an entry here.

The rules this file enforces are CLAUDE.md §5. In short: ideas and facts are not copyrightable,
expression is; same concepts, own structure, own examples, own figures; never a textbook's chapter
sequence, section headings, figures, example programs or problem sets. If a sequence or an example
feels like "the standard way to present this", that is the signal to design a different one.

---

## ch00 · Prerequisites and Setup

**Closest in subject.** Setup and tooling material generally: the MIT 6.1810 tools page, the
xv6 book's preface, the environment appendices in systems textbooks such as *Computer Systems: A
Programmer's Perspective* and *Operating Systems: Three Easy Pieces*, and the many "getting
started with a RISC-V SBC" vendor guides and blog posts.

**How this differs.**

- **Organised around provenance, not around installation.** The chapter's argument is that a
  number's conditions are part of the number, and that the two targets answer different questions;
  the installation steps exist to serve that argument. The comparable material is organised as a
  checklist and stops when the tools are installed.
- **Two targets at once, with an explicit refusal.** No comparable setup chapter sets up an
  emulator and real hardware side by side and then spends its length on what the emulator must
  never be asked. That framing, and the code that enforces it
  (`bench.stamp.provenance_problems`), are the chapter's own.
- **It argues for its own hardware choice from measured evidence.** The section explaining why the
  two targets use different instruction sets — citing a study of RISC-V PMU support and concluding
  against the architecture the rest of the book teaches on — is not a move any comparable setup
  chapter makes. Setup chapters assert their prerequisites; this one shows why it has them and
  what choosing them cost.
- **The examples are original.** `sysfs/include/sysfs/probe.h` — one header compiled against both
  glibc and xv6's freestanding user library, reporting identical structural facts — was written
  for this book, as were the two deliberately-ordered structs used to show padding. Struct padding
  is a standard topic; this pair of structs, this framing (the same members costing different
  amounts) and the cross-target agreement test are not taken from anywhere.
- **The two-architecture disassembly is the chapter's own.** Showing a conditional move against a
  branch is a standard teaching move — *Computer Systems: A Programmer's Perspective* has a
  well-known section on it, and it is the first thing anyone reaches for. Two things here are
  different, and both were chosen because the standard version was the obvious one. The comparison
  is across *architectures* rather than across compiler flags on one, so the point is not "the
  compiler is clever" but "the instruction set does not offer the same choices" — a claim only a
  two-target book can make, and the concrete form of this book's argument for having two targets.
  And `sysfs_clamp` is not anyone's example function: a three-way clamp with two conditionals and
  three exits, picked because base RV64GC has to branch where AArch64 selects. The listings are
  generated from the repository's own compiler (`bench/disasm.py`) and re-checked by CI, not
  transcribed from a book.
- **The problems are original and are tests.** Deciding which of five stamped results may be
  published, predicting a five-member struct's layout before compiling it, and writing a first xv6
  program checked by booting the kernel. No comparable setup chapter has problems at all, let
  alone ones checked by code.
- **The figure is drawn for this book** (`bench/diagrams.py`), and shows a mechanism — what each
  target can and cannot answer — rather than a toolchain diagram.
- **Citations are primary only**: the RISC-V ISA, privileged, psABI and SBI specifications, the
  vendor documentation, and the SiFive core manual. The xv6 book and the textbooks above appear in
  "Where to go next" and are not a source for any of the chapter's content.

---

## ch01 · What a Computer Does With a Program

**Closest in subject.** Every introduction to the C toolchain: the opening chapter of *Computer
Systems: A Programmer's Perspective*, which also walks a program through preprocess, compile,
assemble and link; countless "what gcc actually does" blog posts; and the compiler chapter of any
undergraduate systems course.

**How this differs.**

- **The stages are a means, not the subject.** The comparable material walks the four stages to
  explain what a toolchain is. This chapter walks them to answer a different question — *which of
  this costs anything at run time* — and the walk is over by the third section. What the chapter
  is actually about is the gap between what a programmer wrote and what survives to be executed,
  which is the premise the whole book runs on.
- **The central example is the chapter's own.** Two functions containing the identical loop,
  differing only in whether the bound is visible to the compiler, compiled side by side. The
  standard way to introduce constant folding is a single expression like `2 * 3`; this pairs two
  things a reader would call the same function and shows that one costs nothing and the other
  costs a loop. `sysfs_sum_folded` and `sysfs_sum_counted` were written for this book and the
  listings are regenerated by CI from this repository's compiler.
- **The `hello world` opening is deliberately refused.** A first program that prints a greeting
  has nothing to say about which stages cost anything. This one computes something twice.
- **The numbers are measured, and one of them is a comparison no comparable text makes.** The
  same program linked by glibc and by xv6's user library, side by side, so the reader can see
  that the difference between a tiny binary and a large one is not their code.
- **The problems are original and one of them has no answer key at all.** Problem 1.2 does not
  compare the reader against a stored answer: it performs each edit, runs the toolchain, and
  compares the bytes, so the reader is marked against a compiler. Problem 1.3 is checked by
  disassembling what the reader wrote and looking for a backward branch — a pass condition about
  emitted code rather than about a return value.
- **The figure is drawn for this book** (`bench/diagrams.py`) and shows what each stage
  *discards*, which is the half that explains why the preprocessed file is large and the assembly
  is small.
- **Citations are primary only**: the ELF specification and the RISC-V psABI. CS:APP appears in
  no citation in this chapter.

---

## ch02 · Representing Information

**Closest in subject.** This is the most heavily covered topic in the field. *Computer Systems: A
Programmer's Perspective* chapter 2 is the obvious neighbour — information storage, integer
representations, integer arithmetic — and so is every C book's chapter on types, every "what every
programmer should know about integers" article, and the undefined-behaviour posts that circulate
every few years.

**How this differs.**

- **Organised by failure, not by taxonomy.** The comparable material is a survey: here is
  unsigned, here is two's complement, here is what overflow means, here is floating point. This
  chapter has no survey in it. It is a list of places where the representation *leaks* — where
  two things that look identical in C are not — and each section exists because something breaks
  there. The chapter's own question is "when does that answer bite", and the structure is the
  answer to it.
- **The evidence is disassembly, not derivation.** CS:APP derives the biasing needed for signed
  division by a power of two algebraically. This chapter compiles both divisions and reads what
  came out, then explains the extra instructions. That is the book's method applied consistently,
  and it produces a different chapter: the reader's takeaway is "look at the output", not "here is
  the formula".
- **Undefined behaviour is framed as a licence rather than a hazard.** The standard treatment
  warns that overflow is unpredictable. This one shows a comparison being *deleted* — a function
  returning true without examining its argument — and draws the conclusion that the danger is an
  optimiser acting on an assumption, not a machine misbehaving. The `sysfs_signed_grows` /
  `sysfs_unsigned_grows` pair was written for this book.
- **The figure is drawn from a measurement.** Rather than illustrating padding with an invented
  layout, `bench/diagrams.py` draws both structs byte by byte from offsets the probe measured, so
  the picture cannot disagree with the table and redraws itself on a different ABI. The probe was
  extended in this chapter's commit to report the second struct's offsets for exactly that reason.
- **No bit-level puzzle set.** CS:APP's characteristic exercise is a puzzle with a restricted
  operator list. This chapter's problems are: two operations checked against *properties* rather
  than cases, a packing exercise checked by compiling the reader's ordering, and a hunt for the
  input that breaks a plausible bounds check. The third is deliberately a *defined*-behaviour bug,
  to make the point the chapter closes on.
- **The operations in `sysfs/lib/bits.c` were written for this book**, and the two the problems
  ask for are deliberately absent from it so that nothing in the repository is the answer.
- **Floating point is deferred with a reason given**, rather than covered for completeness: xv6
  does not save floating-point registers across a context switch, which is a decision this book
  can point at and later chapters benefit from.
- **Citations are primary only**: the C standard, the RISC-V unprivileged specification, and the
  psABI.

---

## ch03 · C for People Who Will Read a Kernel

**Closest in subject.** Every C book's chapter on pointers, and in particular *The C Programming
Language* chapter 5, the pointer chapters of *Computer Systems: A Programmer's Perspective*, and
the "pointers are hard" genre generally. Also every "C for systems programmers" course handout.

**How this differs.**

- **Sorted by whether the machine has heard of the construct.** The comparable material is
  organised by language feature: pointers, then arrays, then function pointers, then qualifiers.
  This chapter has one axis and it is not a C axis — *does this survive to the instruction
  stream?* `static` vanishes, an array parameter is discarded, `volatile` survives into every
  load, and a function pointer changes the instruction. That organising question comes from this
  book's spine rather than from C, and it produces a different order and a different selection.
- **It is explicitly not a C tutorial, and says which parts it refuses to cover.** The chapter's
  stated job is to make kernel source readable, so it covers what appears in kernel source and
  stops. No style guidance, no idiom catalogue, nothing about the parts of C xv6 does not use.
- **Each claim is settled by compiling both sides.** `volatile` is not described, it is shown as
  one load against four. The claim that an array parameter is a pointer parameter is not asserted,
  it is checked instruction for instruction by a test, so a compiler that disagreed would fail CI
  rather than quietly making the sentence false. `sysfs/lib/addresses.c` was written for this book.
- **The dispatch-table figure is drawn for this book** and shows the mechanism — a slot holds an
  address, the call is a load then a jump — rather than illustrating a syntax.
- **The problems are original.** 3.1 generates its own listings from the reader's toolchain rather
  than storing them, so the puzzle cannot go stale or disagree with their compiler. 3.2 is a
  storage-duration bug of the shape that made the C library grow `_r` variants, checked by whether
  both answers survive to one `printf`. 3.3 asks the reader to fill a dispatch table where one
  function's name deliberately does not match the slot it belongs in, so it cannot be solved by
  matching strings.
- **`volatile` is bounded rather than recommended.** The chapter states exactly what it
  guarantees and says plainly that it is not a threading primitive, deferring to ch10 — a
  distinction much of the comparable material blurs.
- **Citations are primary only**: the C standard and the xv6 source. The reader is pointed at
  `kernel/uart.c` as a first real thing to read, with a warning about which part of it they are
  not equipped for yet.

---

**Code attribution.** xv6 itself is MIT-licensed and is used as a git submodule, unmodified; the
book's own additions are `xv6/apps/` (Apache-2.0) and `xv6/patches/` (diffs, MIT like what they
patch). See `xv6/README.md` and `LICENSE-CODE`.

---

*Chapters ch01–ch21 are stubs. Entries are added as each is written.*
