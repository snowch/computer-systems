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

## ch09 · Interrupts and Drivers

**Closest in subject.** The xv6 book's chapter on device drivers and interrupts, which walks the
same `uart.c` and PLIC; MIT 6.1810's networking lab; *Operating Systems: Three Easy Pieces* on I/O
devices and interrupts; and the device-driver chapter of any OS text, all of which explain the
top-half/bottom-half split.

**How this differs, and the care taken.**

- **The chapter's finding is a negative result, arrived at by measurement.** A fixed workload
  gives a fixed disk-interrupt count and a varying console-interrupt count, on the same image, run
  after run. The comparable material presents interrupt handling as a mechanism to understand;
  this asks whether it can be counted, finds that the answer depends on what the interrupt
  *means*, and prints only the half that survives. No comparable text reports this because none is
  under an obligation to justify every number it publishes.
- **The zero is the chapter, and it is about the instrument.** xv6's console driver is written to
  sleep when the transmitter is busy, and this measurement shows it never once did: the emulated
  device is never slow. So the book can show the structure and not the pressure that produced it,
  and says so rather than narrating the standard explanation as though it had been demonstrated.
  Turning "what this target cannot show" into the section a reader remembers is this book's shape.
- **The patch counts and changes nothing**, as in ch08 — no driver is added, no policy altered.
- **The filesystem-image dependency is named.** The disk figure depends on `mkfs`'s layout, which
  nothing in the stamping scheme covers; the result records the image's digest and the chapter
  explains why a later chapter will move the number. That is bookkeeping no textbook has, because
  no textbook regenerates its figures.
- **The problems are original.** 9.1 is PLAN's "make the console lose characters" as a bounded-
  buffer predictor with xv6's own buffer size, graded from event strings the test wrote. 9.2 asks
  for a count and requires "undecidable" for the device whose count the workload does not
  determine. 9.3 is graded *against the machine* — the test boots several times and compares
  censuses — and degrades to "inconclusive" rather than failing a reader when the experiment
  cannot settle a counter. A problem whose answer key is the hardware's own behaviour is not a
  form any of the comparable material uses.
- **Deliberately not set**: adding a driver for a virtual device, which was in the plan and which
  is close to a well-known lab, and which no test could grade without becoming one.
- **Citations are primary only**: the RISC-V privileged specification and xv6's own source.

## ch10 · Locks and Memory Ordering

**Closest in subject.** The xv6 book's chapter on locking, which walks the same `spinlock.c`; MIT
6.1810's locks lab; *Operating Systems: Three Easy Pieces* on locks and concurrency; and the
memory-ordering material in *A Primer on Memory Consistency and Cache Coherence* and in the RISC-V
and ARM architecture manuals.

**How this differs, and the care taken.**

- **The chapter is built on disassembly rather than on narrative.** "Two threads can lose an
  update" is presented as a fact about what `counter++` compiles to, printed on both
  architectures, rather than as a story about threads. Every claim about atomicity and ordering is
  a listing CI regenerates, which is a form none of the comparable material uses.
- **Atomicity and ordering are separated by showing that the spelling changes and the instruction
  count does not.** `amoadd.d` against `amoadd.d.aqrl` is the same single instruction with two
  letters added. That framing — ordering is free here in instructions and is not free everywhere —
  is this book's, and it sets up ch18 rather than restating a memory-model chapter.
- **The AArch64 outlined-atomics finding is original to this measurement.** The same C becomes one
  instruction on RISC-V and a call to a run-time-dispatched helper on AArch64, because the
  compiler cannot assume LSE. It was found by disassembling both, not taken from anywhere.
- **The kernel primitives are read out of the kernel as built**, so the counts are of the
  instructions the machine runs. The three observations drawn from them — one instruction of
  twenty-five does the mutual exclusion, `release` contains no atomic at all, and `push_off`
  plus `pop_off` outweigh both primitives — are this book's, and follow from counting rather than
  from reading the source.
- **ch09's debt is paid explicitly.** The book's own unlocked census counters are judged against
  the chapter's own evidence, and defended on the grounds that locking the trap path would change
  the thing being measured by an amount comparable to what is being counted. A book auditing its
  own instrumentation in the chapter that explains why it is wrong is not a move any textbook
  makes, because no textbook has instrumentation to audit.
- **A plan that turned out to be wrong is reported rather than rewritten.** PLAN.md promised
  contention counts and claimed the interleavings would be deterministic under QEMU; neither
  survived, and "What we measured" says so and says why. `bench/outline.py` is corrected in the
  same commit.
- **The problems are original.** 10.1 is graded by running the reader's lock under real threads
  and counting lost updates — the only problem in the book graded by concurrency, because a lock
  is the one thing that cannot be checked by reading it. 10.2's eighteen cases turn on the
  asymmetry of acquire and release and on same-address ordering, which settles a case before any
  barrier is consulted. 10.3 asks for an order conflict rather than "will it hang", which is
  deliberately the question a lock-ordering rule actually asks. Verified against references kept
  outside the repository.
- **Not set**: the well-known allocator-and-buffer-cache contention lab, which measures contention
  — the one thing this target cannot show.
- **Citations are primary only**: the RISC-V unprivileged specification and xv6's own source.

## ch11 · Scheduling and Context Switches

**Closest in subject.** The xv6 book's chapter on scheduling, which walks the same `swtch`,
`sched` and `sleep`; MIT 6.1810's threads lab; *Operating Systems: Three Easy Pieces* on
scheduling policy and on the abstraction of a thread.

**How this differs, and the care taken.**

- **The chapter's spine is a ratio the comparable material does not compute.** A trap saves
  thirty-one registers and a switch saves fourteen, both read out of this book's own earlier
  measurement and out of the kernel as built. The explanation — a trap is not a call and a switch
  is, so ch04's convention has already done most of the work — reuses this book's own chapters
  rather than restating background, and turns "context switches are expensive" into a claim with a
  number attached.
- **Switches are attributed by reason, and only the workload-determined one is published.** That
  discipline is this book's and is applied for the fourth time here; the chapter states it briefly
  rather than re-deriving it, and reports the finding that the timer never preempted anything in
  this workload without publishing the count.
- **The patch's first version contained ch10's race**, a shared reason-slot written by one hart and
  read by another, and the count came out twice what the workload could have caused. It is fixed
  with a per-process field and the patch's own comment says so. A book that gets caught by the
  chapter it just wrote, and prints that, is not a form any textbook uses.
- **The problems are original.** 11.1 grades ch04's convention applied to the switch, so the
  chapter's headline ratio becomes something the reader derives rather than reads. 11.2 uses two
  orderings of the same six events with different answers, so the problem cannot be passed by
  recognising a diagram. 11.3 picks burst lengths on which no two policies agree, so a reader who
  implements one policy three times fails. Verified against references kept outside the repository.
- **Not set**: the well-known kernel-threads lab, which asks for an implementation of switching
  itself — the one thing this chapter can simply show the reader, disassembled.
- **Citations are primary only**: xv6's own source.

## ch12 · The File System

**Closest in subject.** The xv6 book's chapters on the file system and on logging; MIT 6.1810's
file-system and large-files labs; *Operating Systems: Three Easy Pieces* on file-system
implementation, journalling and crash consistency; and the journalling chapter of any OS text.

**How this differs, and the care taken.**

- **The chapter opens with a measured amplification factor and explains the file system in order
  to explain it.** The comparable material introduces the seven layers and then mentions that a
  log doubles writes. Here the number comes first, measured, and each layer is introduced as the
  reason one of the counted blocks exists.
- **The figure is a difference between two runs, not a single measurement.** A program creates,
  optionally writes one byte, closes and unlinks; the census is zeroed before each run; the byte's
  cost is the subtraction. That method exists because a single run charges the byte for forking
  and exec'ing the program, which is larger than the thing being measured — and stating the method
  in the chapter is part of the point.
- **The runner refuses to stamp a result that contradicts the chapter's own explanation.** Twice
  the blocks plus twice the transactions is checked, not asserted, so a kernel change that broke
  the explanation would fail CI rather than leave the prose quietly wrong.
- **That cross-check caught a real error in this chapter's own instrumentation.** The counter first
  counted `log_write` calls rather than blocks, xv6 absorbs repeated writes to the same block, and
  a simpler invariant passed on two wrong numbers agreeing. The comment in `run_blocks.py` records
  it.
- **Idempotence is given its own section and treated as the load-bearing idea**, with the
  consequence drawn that the log must hold blocks rather than changes — which is also the
  explanation for the amplification. That framing is this book's.
- **The problems are original.** 12.1 is graded against the chapter's own measurement as well as
  against arithmetic, so a formula that fits the algebra and not the machine fails. 12.2 finds the
  single commit point. 12.3 gives six orderings of the same three writes, all of which produce the
  right end state if nothing goes wrong, and asks which is safe at every point — deliberately not
  "which looks sensible". Verified against references kept outside the repository.
- **Not set**: the well-known large-files and symbolic-link labs, which are implementation
  exercises rather than questions about what the disk is charged.
- **Citations are primary only**: xv6's own source.

## ch13 · The Same Program on Both Targets

**Closest in subject.** No single work is close, which is unusual for this book. The nearest
material is the "measurement is hard" literature — Mytkowicz et al. on measurement bias, and the
introductory chapters of *Performance Analysis and Tuning on Modern CPUs* and *Systems
Performance* — and the pointer-chase microbenchmark, which is folklore and appears in many places.

**How this differs, and the care taken.**

- **The chapter exists because of this book's own structure and could not be lifted from
  anywhere.** It is the hinge between a target chosen for visibility and a target chosen for
  cost, and its argument is about the twelve chapters that precede it.
- **The program is chosen so the structural model is right and useless at once.** Two routes over
  the same data, the same answer, and loop bodies differing by one load — so Parts I and II
  predict a factor under two, correctly, and Part III exists because of the size of the error.
  The pointer chase is a well-known shape; using it as the moment a book's own method runs out is
  not.
- **The confound is named as three simultaneous variables and then turned into an exercise.**
  Problems 13.1 and 13.2 grade the design of the comparison rather than its result, against a
  table of configurations the tests read for themselves, so there is no key. That is this book's
  own move and the reason the chapter is placed where it is.
- **"Structure transfers and cost does not" is argued to be wrong in both directions.** The
  instruction count is structural and does not transfer; the layout is structural and transfers
  only because ch02 measured that it does. Problem 13.3 is built on exactly those two.
- **The central figure is pending and the chapter says so in its own voice**, with a paragraph on
  why an emulated duration would be worse than no duration. Writing the argument so that it
  stands without the number, and landing the number later as a one-command change, is this book's
  pending-figure discipline used where it matters most.
- **Citations**: the measurement-bias paper is cited as a primary source in "Where to go next";
  no textbook is used for content.

## ch14 · Measuring

**Closest in subject.** *Performance Analysis and Tuning on Modern CPUs* and *Systems Performance*
both open with measurement methodology; Mytkowicz et al. on measurement bias; the benchmarking
advice in the Google Benchmark and Criterion documentation; and "how to benchmark" blog posts
without number.

**How this differs, and the care taken.**

- **The chapter is placed and shaped by this book's own argument.** It exists because ch13 has just
  shown the structural model failing, and it measures the instrument before anything is measured
  with it. Its four sections are the four ways this book's own figures could be wrong.
- **Measurement bias is demonstrated rather than cited**, by an experiment the reader runs: the
  same binary, the same work, three answers, differing only in how many bytes of stack were
  claimed first. The paper is credited for the finding and the experiment here is this book's.
- **Thermal throttling is treated as a measurement hazard rather than a hardware fact**, because
  the reference machine does it — the clock moves under the benchmark and a comparison run
  back-to-back can rank two implementations by which went first. That framing follows from the
  board this book chose and is why every host result stamps the machine's state.
- **The library deliberately provides no "benchmark this function" macro**, and the header says
  why: deciding what to repeat, what to warm up and what to report is the skill, and a macro that
  made those decisions invisibly would remove it.
- **Problem 14.4 has no test and no known answer**, and asks the reader to falsify a claim ch00
  makes about this book's own setup advice. Handing a reader an unmeasured claim from your own
  text and inviting them to knock it down is not a form any comparable work uses.
- **The problems' keys are computed from the definitions rather than written down**, and 14.3's
  definition has a second clause — the discarded prefix must actually have been slow — that exists
  because the first draft of it let a mid-run spike justify throwing away every good measurement
  before it. The scaffolding test caught that, which is recorded in the stub's own comment.
- **`sysfs/lib/timing.c` joins the fingerprint for `host` results only.** The plan said it would
  join CORE_SOURCES and invalidate every host result once; in fact CORE_SOURCES invalidates
  everything, and would have done so on every future edit to the clock. The mechanism is now
  target-aware and `bench/stamp.py` records why.
- **Citations are primary only**: the measurement-bias paper and the Linux manual pages. The
  benchmarking textbooks are not cited at all.

## ch15 · The Memory Hierarchy

**Closest in subject.** *What Every Programmer Should Know About Memory* (Drepper); *Computer
Systems: A Programmer's Perspective* chapter 6, including its memory-mountain figure; *Performance
Analysis and Tuning on Modern CPUs* on the memory subsystem; and the lmbench and MemLat
microbenchmark literature. The pointer-chase latency probe is long-standing folklore.

**How this differs, and the care taken.**

- **The chapter's job is set by ch13 rather than by the topic.** It exists to explain a specific
  earlier prediction failing, and it closes by judging that prediction — the extra load was never
  the difference; the difference is that one program can overlap its accesses and the other
  cannot. That arc belongs to this book.
- **Deliberately not a memory mountain.** The obvious figure here is the two-dimensional
  size-against-stride surface that CS:APP made famous, and it is not used. The three experiments
  are separate one-dimensional curves, each answering one question, and the reason is this book's
  policy that a figure must show a mechanism rather than a landscape.
- **The instrument's shape is argued rather than assumed.** A dependent chase measures latency and
  an independent walk measures parallelism; the chapter says which it built and why, and says that
  every number it produces is therefore a worst case.
- **The TLB section is ch07's cost, in ch07's own terms.** Three levels of page table become three
  extra memory accesses, and the counter-intuitive consequence — data fitting in cache while
  translations do not — is drawn out because this book has already made the reader build the walk.
- **The vendor comparison is a stated policy, not a check.** Where the datasheet and the
  measurement disagree, the book prints the measurement and discusses the disagreement, which
  ch00 established and this is the first chapter to exercise.
- **The problems are curve-reading rather than fact-recall**, graded against synthetic curves the
  tests construct — including one that drifts upward without stepping, and one flat stride curve
  whose correct answer is that it has none. Verified against references kept outside the
  repository.
- **Citations are primary only**: the SoC documentation and the core's technical reference manual.
  Drepper and CS:APP are not cited, here or anywhere.

## ch16 · Optimising Code

**Closest in subject.** *Computer Systems: A Programmer's Perspective* chapter 5, which is the
canonical treatment of hand-optimising a loop and measuring each step; *Performance Analysis and
Tuning on Modern CPUs* on compiler transformations; and Agner Fog's optimisation manuals.

**How this differs, and the care taken.**

- **CS:APP's chapter 5 applies transformations and shows each one helping. This chapter applies
  them and finds that three of the five produced identical code.** That is the opposite
  conclusion, it was measured rather than chosen, and the chapter is arranged around it: the
  question is not "how do I optimise this loop" but "which of these am I doing for nothing".
- **The backfiring case is the chapter's second finding and was not planned.** Hand-unrolling
  produced substantially more instructions than the plain source at `-O2` and the gap widened at
  `-O3`, because the hand-written version is harder for the compiler to analyse. The plan asked
  for "at least one case where the optimisation does nothing"; the measurement supplied something
  better.
- **The figure is a real result rather than a pending one, in a Part III chapter.** Instruction
  counts are compiler output, so CI regenerates them every push, and the chapter's claims about
  this compiler are continuously checked against this compiler. What the surviving differences
  cost is separated out, declared pending, and explicitly not claimed.
- **Problems 16.1 and 16.2 are graded against the book's own stamped result**, so a future
  compiler that changes its mind changes the right answer rather than making the book wrong. That
  is a form this book invented for ch09 and this is its cleanest use.
- **Problem 16.3 is graded by compiling.** Five functions, identical arithmetic, differing in what
  becomes of the result; the test compiles them and counts, and the threshold follows the compiler
  rather than being asserted. The two traps — a store to a variable nothing reads, which is
  removed, and a condition that is never true, which is not — were found by running it.
- **Citations are primary only**: the compiler's own manual page. No optimisation textbook is
  cited.

## ch17 · The CPU

**Closest in subject.** *Performance Analysis and Tuning on Modern CPUs* on the out-of-order
pipeline and top-down analysis; Agner Fog's microarchitecture manual; *Computer Architecture: A
Quantitative Approach* on ILP and branch prediction; and the multiple-accumulator example, which
is folklore and appears in CS:APP chapter 5 among many others.

**How this differs, and the care taken.**

- **The chapter opens by failing, and that is the content.** It set out to measure branch
  misprediction and found the compiler had replaced the branch with a conditional increment, so
  there was nothing to mispredict. The finding is stamped, CI checks it still holds, and the
  chapter is arranged around it — a measurement of branch prediction on that loop would have
  produced a number about something else entirely.
- **Problem 17.1 records that this book predicted wrongly**, in the stub the reader edits. Inviting
  the reader to beat the author at a prediction the author got wrong is not a form the comparable
  material uses.
- **The accumulator example is used against instruction counts rather than for speed.** Its point
  here is that the shortest program is the slowest, which closes ch16's explicit deferral; the
  instruction counts that make that visible are stamped and regenerated rather than asserted.
- **Problem 17.2's model is presented with its own limit.** The formula predicts more accumulators
  are always better; the stub and the scaffolding test both say what actually stops it — register
  pressure, which is nowhere in the formula — because a model that is right about what it models
  and silent about what limits it is the usual kind.
- **Derived counters are given a section and a labelling rule.** The cost of a mispredict is a
  slope rather than a measurement, the table says "derived" in its own row, and the chapter states
  the general policy for PMU events that are computed rather than counted. That discipline is this
  book's.
- **Citations are primary only**: the core's technical reference manual and `perf list`.

## ch18 · Memory Ordering on Real Hardware

**Closest in subject.** *A Primer on Memory Consistency and Cache Coherence*; the false-sharing
sections of *What Every Programmer Should Know About Memory* and *Performance Analysis and Tuning
on Modern CPUs*; the ARM and RISC-V memory-model chapters; and the very large literature on
Amdahl's law.

**How this differs, and the care taken.**

- **The chapter's reason for existing is the book's two-architecture decision, and it says so.**
  Its middle section puts AArch64's `stlr` beside RISC-V's `fence rw,w` — both printed by ch10
  from real disassembly — and draws the conclusion that a reader shown one weak memory model
  concludes that model is memory ordering. No single-architecture treatment can make that move,
  and it is the return on a cost PLAN §5 paid two chapters of Part III for.
- **The false-sharing figure needs no machine and is measured anyway.** Whether two counters land
  on one line is decided by the layout, so it is stamped from a cross build, and the runner
  refuses a layout in which the packed structure has stopped sharing or the padded one has
  started — which would leave the chapter demonstrating nothing while still producing a table.
- **"False sharing" is examined as a name.** The sharing is real and what is false is the
  implication that the program meant to share; problem 18.1's key case is two fields on one line
  written by the same thread, which costs nothing.
- **Amdahl's law is used as a pre-registration rather than as a result.** The chapter's claim is
  that a measured curve alone says very little and a measured curve falling short of a predicted
  one says where to look. Problem 18.2 is therefore set to be done *before* the board reports.
- **"Atomics are expensive" is refused as a fact about atomics.** The two columns of the cost
  table are the same instruction differing by a large factor on something not in the instruction.
- **The limitation section separates what the machine does from what the model permits**, and says
  that no measurement can replace ch10's problem about permission — a reordering that never
  happens on this chip may be allowed on the next one.
- **Citations are primary only**: the two architectures' specifications.

## ch19 · The OS Layer's Cost on Real Hardware

**Closest in subject.** The system-call and page-fault chapters of *Operating Systems: Three Easy
Pieces* and of the xv6 book; *Systems Performance*'s treatment of system-call overhead and its
`syscall`-latency methodology; *Computer Systems: A Programmer's Perspective*'s exceptional-control-flow
chapter; and the many published "how expensive is a system call" microbenchmarks.

**How this differs, and the care taken.**

- **The chapter is built as a verdict on Part II rather than as an introduction to anything.**
  Its first figure is Part II's own counts, gathered from three results the book already
  committed, and its job is to turn them into a bound that the measurement can contradict. No
  existing treatment can do that, because no existing treatment spent seven chapters counting the
  same three services on a kernel the reader can stop mid-trap.
- **The one measured figure is a pair of listings, and the pairing is the argument.** `getpid`
  written as the trap instruction, and `getpid` written the way anybody writes it — a frame, a
  branch and a sign-extension, with the trap nowhere in the listing. The conclusion drawn is that
  cost at this layer is not visible in the code, which is then the reason the vDSO section lands.
  The example is the book's own `sysfs/lib/oscalls.c`, not anyone's.
- **The calling-convention observation is derived, not recited.** The register holding the call
  number is not one the C convention would pick, and the chapter's reason is that the process and
  the kernel were compiled separately and so cannot have agreed by being compiled together —
  which is ch04's argument about callee-saved registers, reused rather than restated.
- **Problem 19.1 is deliberately not the standard "beware of measurement overhead" warning.** It
  is arithmetic whose interesting property is that at a single iteration the two harnesses agree:
  putting the clock outside the loop divides the overhead rather than removing it. The test
  asserts that agreement as scaffolding.
- **Problem 19.2 is a lower bound, and the chapter says what each of the three possible outcomes
  would mean** — under it the model is wrong, a little over it the model explains the cost, far
  over it the model was never the expensive part. The problem's own test refuses a key that has
  been rounded twice.
- **Problem 19.3 is a precedence, not a taxonomy.** The four facts are classified in a stated
  order, and the scaffolding tests assert the three things the order is for: fatal dominates, an
  existing translation short-circuits, and a page owing only zeroes is minor with nothing
  resident. All sixteen combinations are checked, so no case is quietly excluded.
- **The limitations section refuses the chapter's own headline.** It says plainly that this cannot
  tell you what a system call costs — `getpid` was chosen because the kernel does almost nothing
  after the trap, so what is reported is the floor of the boundary, and a `read` returning a
  megabyte is mostly not that.
- **Citations are primary only**: the ARM architecture reference manual for the exception model,
  and Linux's own generic system-call table for the number in the listing.

## ch20 · Whole-Machine Profiling

**Closest in subject.** *Systems Performance*'s profiling and flame-graph chapters; *Performance
Analysis and Tuning on Modern CPUs* on `perf` and on skid; the `perf` wiki and tutorial; the
profiling chapter of *Computer Systems: A Programmer's Perspective*; and the large body of
writing on sampling profilers' pitfalls.

**How this differs, and the care taken.**

- **The chapter's method is a pre-registration, and that is its actual contribution.** The program
  is censused — records, table width, lines reached, how lopsided the decoy branch is — and the
  census is stamped and committed *before* any profile exists. The stated reason is that a profile
  with nothing written down beforehand is trivially easy to agree with. No treatment consulted
  does this; they profile first and explain afterwards.
- **The runner enforces the pre-registration.** `bench/run_profile.py` refuses to stamp a census
  in which the two arrangements stop agreeing, the scattered pass stops reaching every cache line,
  or the conditional stops being lopsided — each of which would leave the chapter confidently
  pointing at the wrong phase while still producing a table.
- **The example program is the book's own and is built round a specific misdirection.** The phase
  with the conspicuous arithmetic and a conditional is cheap; the phase that is three lines long
  is the cost. Neither the program nor the misdirection is anyone else's, and the payoff is a
  census row the reader can already interpret from ch17 and ch18.
- **The line-holds-a-run observation is reused rather than introduced.** That the keys miss two
  thirds of the counters and still touch every line is ch18's coherence-works-in-lines argument
  reappearing as a capacity argument, and the chapter says so rather than presenting it fresh.
- **Skid is derived from the mechanism rather than stated as a caveat.** The diagram draws the
  counter overflowing into an interrupt — ch09's mechanism, met already, doing a job unrelated to
  a device — and the attribution error follows from that, with the chapter's rule being "read the
  neighbourhood, never the line".
- **Problem 20.3 is the chapter's original contribution to a well-worn topic.** Aliasing between a
  fixed sampling period and a fixed loop period is reduced to a number of visited positions, from
  which the reason real profilers randomise the period follows arithmetically rather than by
  assertion. The scaffolding shows a one-cycle change taking a profile from one position to all
  of them.
- **Problem 20.2 asks for a derivation, not a rule of thumb.** The closed form for how many
  samples a share needs is the reader's to find, and the tests assert the two properties worth
  carrying around — quartering behaviour in the width, and that a rare symbol is cheap to resolve
  only in its own terms.
- **The limitations section refuses the chapter's own frame** — it says that a profile is a map of
  where time went and not of what is responsible, and that this chapter's own expensive phase is
  expensive because of a decision made in a different phase that no amount of sampling points at.
- **Citations are primary only**: `perf_event_open(2)` and the measurement-bias paper.

---

**Code attribution.** xv6 itself is MIT-licensed and is used as a git submodule, unmodified; the
book's own additions are `xv6/apps/` (Apache-2.0) and `xv6/patches/` (diffs, MIT like what they
patch). See `xv6/README.md` and `LICENSE-CODE`.

---

*Chapters ch01–ch21 are stubs. Entries are added as each is written.*
