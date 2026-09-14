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

## ch04 · Machine-Level Code on RISC-V

**Closest in subject.** *Computer Systems: A Programmer's Perspective* chapter 3, which is the
canonical treatment of machine-level code and procedure calls; *The RISC-V Reader*; the machine
code chapters of Patterson & Hennessy; and every "reading assembly" tutorial.

**How this differs.**

- **No instruction reference and no register table.** The comparable material introduces the
  architecture — here are the registers, here is what each one is for, here are the instruction
  formats. This chapter contains none of that, deliberately: the register groupings live in
  Appendix A where a reference belongs, and the chapter teaches the *rule* that decides which
  group a register is in, because the rule is short and the table is not worth memorising.
- **The calling convention is derived from a lifetime question, not presented as a fact.** The
  chapter's framing is that there are only two possible answers to "who preserves this register",
  that a convention picks both, and that the consequence is about where a value must live given
  how long it must survive. That reasoning is what lets a reader predict a prologue rather than
  recall one, and it is the basis of two of the three problems.
- **The frame measurement is the chapter's own, and its conclusion is not the usual one.** Four
  functions compiled at `-O0` and `-O2`, with frame size, instruction count and memory-operation
  count side by side. The finding that gets the emphasis is that an optimiser's principal job here
  is *keeping values in registers rather than memory* — `sysfs_many_locals` goes from a hundred-odd
  bytes of frame and thirty memory operations to none of either — rather than the usual framing of
  optimisation as cleverer arithmetic.
- **`sysfs/tools/framewalk.c` was written for this book**, and its `noinline` attributes are
  presented as the lesson rather than as scaffolding: a frame is a call the machine still makes,
  which is why a backtrace is shorter than the source.
- **The figure draws the stack growing downwards** with the two walkable slots marked and the
  two-line walk beside it, and its footnote bounds the claim to builds that keep frame pointers.
- **The problems are original and mechanically checked against a compiler.** 4.1 asks for a
  reconstruction that matches instruction for instruction rather than behaviourally — the target
  listing is generated by the test, never stored. 4.2 asks for predictions about four prologues and
  reads the answers out of the disassembly. 4.3 asks the reader to name registers from each half of
  the convention and checks both the disassembly and the ABI class, so an answer that is
  mechanically true but comes from the wrong group is rejected with the reason.
- **Citations are primary only**: the psABI, the unprivileged ISA specification, and xv6's own
  `swtch.S`, which the reader is sent to read as fourteen lines they can already decode.

---

## ch05 · Linking and Loading

**Closest in subject.** *Computer Systems: A Programmer's Perspective* chapter 7 is the canonical
treatment of linking; *Linkers and Loaders* (Levine) is the book-length one; and there is a large
genre of "ELF explained" articles and annotated hexdumps.

**How this differs.**

- **The reader is written, not used.** The comparable material explains the format and shows
  `readelf` output. This chapter's premise is that a format explained by a tool stays a thing only
  the tool understands, so `sysfs/tools/elfdump.c` was written for this book with no `<elf.h>`
  anywhere in it — the structures are declared from the specification, field offset by field
  offset, and the chapter's measurements come from that reader rather than from `readelf`.
- **Organised around the sections/segments distinction as the chapter's spine**, rather than as
  one topic among linking, symbol resolution, static libraries, dynamic libraries and loading. The
  claim the chapter builds to — an ELF executable is a set of instructions to a loader, and the
  code is incidental — is this book's framing, and follows from its "what does the machine
  actually act on" question rather than from the usual "how does a program get built" one.
- **The `.bss` observation is given its own section and a consequence.** A segment whose memory
  size exceeds its file size is used to make the point that zero-initialisation is the *cheapest*
  initial state rather than a favour with a cost — which is the opposite of how it is usually
  presented.
- **Dynamic linking is deliberately excluded and the exclusion is justified.** xv6's statically
  linked, fixed-address binaries are chosen precisely because a Linux binary's answer is
  complicated by machinery that is not the mechanism underneath. Most comparable chapters cover
  both and blur which is fundamental.
- **The figure is generated from the stamped result**, so the collapse from sections to segments
  it draws is this repository's actual binary rather than an illustrative one.
- **The problems are original and none has a stored answer.** 5.1 asks for two functions the
  book's own reader deliberately does not contain, checked against that reader's output on a real
  binary so the target moves with the file. 5.2 asks for link predictions and actually links the
  pairs, including one case that links successfully and produces a wrong program. 5.3 generates
  four real linker failures during the test run — including an archive listed before the object
  that needs it — and asks the reader to name the cause from the message.
- **Citations are primary only**: the ELF specification, the psABI, and xv6's own `exec.c`, which
  the reader is sent to as the shortest complete answer to "what happens when you run a program".

---

## ch06 · Traps and System Calls

**Closest in subject.** The xv6 book's chapter on traps and system calls, which walks the same
`trampoline.S` and `usertrap` on the same kernel; MIT 6.1810's system-call lab; *Operating Systems:
Three Easy Pieces* on limited direct execution; and the trap chapter of any OS text.

**How this differs, and the care taken.** This is the chapter where the closest neighbour is the
documentation for the very kernel being read, so the separation is deliberate and specific.

- **The xv6 book explains the code; this chapter measures it.** Its central artefacts are a count
  of the trap path's length read out of the built kernel, and a census of what a fixed workload
  actually asked for, read out of a running one. Neither appears in the comparable material,
  which is narrative.
- **The framing is "a trap is not a call", derived from ch04.** The chapter's argument runs from
  the calling convention: a called function preserves callee-saved registers because both sides
  agreed; an interrupted program agreed to nothing, so the path must save everything. That
  reasoning is this book's, it reuses ch04's material rather than restating background, and it
  sets up the register problem.
- **The kernel patch is not the MIT lab.** 6.1810's syscall lab asks for `trace(mask)` and
  `sysinfo()`. This book's patch is a per-cause trap census printed on Ctrl-T, mirroring xv6's
  existing Ctrl-P convention rather than adding a system call — specifically so that "add a system
  call end to end" remains the reader's problem rather than the chapter's worked example.
- **A measurement is deliberately withheld, and the withholding is taught.** Interrupt counts are
  not recorded because their frequency depends on how long things took, and elapsed time inside
  QEMU is a property of the host laptop. The chapter explains the decision rather than quietly
  omitting the number. No comparable text confronts this, because no comparable text is trying to
  hold a line about what its target may be asked.
- **The figure is drawn from the stamped result**, so it cannot claim a path length the
  measurement does not support.
- **The problems are original.** 6.1 is checked behaviourally — the count must be non-zero and must
  grow between two runs, so a constant fails — rather than by inspecting the reader's source. 6.2
  reads the register count out of the kernel as built, so a reader who patches the trampoline is
  graded against their own kernel.
- **Citations are primary only**: the RISC-V privileged specification and xv6's own source. The xv6
  book is not cited here or anywhere except "Where to go next" in other chapters, and this chapter
  does not send the reader to it at all — it sends them to the assembly.

## ch07 · Virtual Memory

**Closest in subject.** The xv6 book's chapter on page tables, which walks Sv39 and `vm.c` on the
same kernel; *Operating Systems: Three Easy Pieces* on paging and multi-level page tables;
*Computer Systems: A Programmer's Perspective* chapter 9; and the memory-management chapter of any
OS text. The RISC-V Reader's treatment of Sv39.

**How this differs, and the care taken.** The comparable material asks how translation works. This
chapter asks what the map costs, which produces a different spine, a different measurement and
different problems.

- **The organising question is the cost of the description, not the mechanism of the lookup.** A
  page table is a data structure that exists so an address can mean something, and it occupies
  memory. The chapter's central measurement is how many physical pages two real address spaces
  spend describing where their other physical pages are — a figure no comparable text reports,
  because none of them is asking the book's question.
- **The finding is the inversion, and it was measured rather than chosen.** The kernel's map is
  vast and nearly free per page; init's is tiny and mostly overhead. That contrast, and the
  explanation for it — cost follows the number of separate regions, not the number of pages — is
  arrived at from a census this book's patch prints, not from any existing exposition.
- **Sv39's geometry is derived, not recited.** The chapter's claim is that only the page size and
  the entry size were chosen and every other number is forced. That framing is this book's, it
  matches ch04's treatment of the calling convention, and it produces a table whose right-hand
  column is "where it comes from".
- **The kernel patch is not a lab exercise from any course.** It is a page-table census on Ctrl-V,
  mirroring xv6's own Ctrl-P convention and this book's own ch06 patch. MIT 6.1810's page-table
  labs ask for `vmprint`, a speed-up of `getpid` via a shared page, and a superpage allocator;
  none of those is this, and the chapter deliberately does not set them.
- **The cross-check is the unusual part.** `sysfs/tools/sv39.c` derives the required table count
  from the addresses alone, from the specification, with no machine involved; the kernel counts
  its tables by walking them; the runner refuses to stamp a result in which the two disagree. The
  published figure is therefore an agreement between a specification and a kernel rather than a
  single observation. No comparable text does this because none of them is stamping results.
- **ch06 is repaid in this chapter's currency.** The trapframe and trampoline cost two page-table
  pages per process, because nothing else is within a gigabyte of them. That is a consequence of
  the previous chapter's mechanism, expressed in a unit the previous chapter could not measure,
  and it is this book's observation.
- **The problems are original and none has a stored answer.** 7.1 is graded by how many pages the
  reader's mapper took from the allocator, compared against the chapter's own model — so a correct
  mapper that allocates eagerly fails, which is the chapter's thesis turned into a test. 7.2 is
  graded against the mappings the reader's own 7.1 made. 7.3's four answers each follow from where
  the test put the mappings. `sysfs/lib/sv39.c` splits addresses and counts tables; it neither
  walks a page table nor builds one, so it hands the reader nothing.
- **Citations are primary only**: the RISC-V privileged specification and xv6's own source. The
  xv6 book is not cited, and the chapter sends the reader to `vm.c` rather than to any commentary
  on it.

## ch08 · Page Faults as a Feature

**Closest in subject.** The xv6 book's chapter on traps and page faults; MIT 6.1810's lazy-
allocation and copy-on-write labs, which set exactly the two features this subject suggests;
*Operating Systems: Three Easy Pieces* on paging mechanisms and swapping; and the demand-paging
section of any OS text.

**How this differs, and the care taken.** This is the chapter where the obvious exercises are two
famous assignments, so both are deliberately not set — and the reason is not only originality.

- **The chapter implements no policy, because this kernel already has both.** The xv6 revision
  used here ships `sbrk` and `sbrklazy` and lets a program choose per call. So there was nothing
  to build, "implement lazy allocation" cannot be an exercise, and the patch is counters only. The
  book's contribution is the question neither policy answers about itself.
- **The organising idea is the exchange rate, which the comparable material omits.** Laziness is
  almost always described by its saving. This chapter puts both sides of the trade in one table:
  pages never allocated, against entries into the kernel bought with them, for one workload chosen
  to bracket the trade rather than to demonstrate a win.
- **Copy-on-write is named, explained as one more test on the same hook, and explicitly not
  measured.** That is stated in "What this cannot tell you" rather than quietly skipped, because
  naming a mechanism and pricing it are different things. It is also why no exercise here asks for
  a COW fork.
- **The second cost is this book's own emphasis.** Laziness moves a failure from the return value
  of a call, where a program can handle it, to an ordinary store, where it cannot — which is why
  an overcommitting system needs something to kill processes with. The chapter derives it, and
  problem 8.3 makes the reader compute it.
- **The problems are the handler's decisions, lifted out of the kernel.** 8.1 is the bytes-against-
  pages trap, with overlapping and unordered runs. 8.2's nine cases include the two a handler
  written from the happy path gets wrong — the exact boundary, and a page that is already mapped,
  where allocating would map a blank page over live data. 8.3 is the failure-visibility question.
  All answers follow from what the test itself constructed; nothing is stored, and the patch
  decides nothing, so it hands the reader no answer.
- **Determinism is by construction.** `faultload` fixes and prints every quantity, the kernel
  counts independently, and the runner refuses a result in which they disagree, one latched from
  the wrong process, or one in which the handler declined a fault. That machinery is this book's
  and exists because ch06 was got wrong first.
- **Citations are primary only**: the RISC-V privileged specification and xv6's own source.

---

**Code attribution.** xv6 itself is MIT-licensed and is used as a git submodule, unmodified; the
book's own additions are `xv6/apps/` (Apache-2.0) and `xv6/patches/` (diffs, MIT like what they
patch). See `xv6/README.md` and `LICENSE-CODE`.

---

*Chapters ch01–ch21 are stubs. Entries are added as each is written.*
