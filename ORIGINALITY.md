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
- **The problems are original and are tests.** Deciding which of five stamped results may be
  published, predicting a five-member struct's layout before compiling it, and writing a first xv6
  program checked by booting the kernel. No comparable setup chapter has problems at all, let
  alone ones checked by code.
- **The figure is drawn for this book** (`bench/diagrams.py`), and shows a mechanism — what each
  target can and cannot answer — rather than a toolchain diagram.
- **Citations are primary only**: the RISC-V ISA, privileged, psABI and SBI specifications, the
  vendor documentation, and the SiFive core manual. The xv6 book and the textbooks above appear in
  "Where to go next" and are not a source for any of the chapter's content.

**Code attribution.** xv6 itself is MIT-licensed and is used as a git submodule, unmodified; the
book's own additions are `xv6/apps/` (Apache-2.0) and `xv6/patches/` (diffs, MIT like what they
patch). See `xv6/README.md` and `LICENSE-CODE`.

---

*Chapters ch01–ch21 are stubs. Entries are added as each is written.*
