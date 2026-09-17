# Errata and known gaps

Two lists. The first is for things that were **wrong** — including anywhere a later chapter
contradicts an earlier one, in which case the fix goes in the earlier chapter (CLAUDE.md §6). The
second is for things that are **not finished**, recorded so they are not mistaken for oversights.

## Corrections

| Date | Chapter | What was wrong | Fixed in |
|---|---|---|---|
| 2026-09-14 | ch00, PLAN §5 | Part V was planned on RISC-V hardware. No purchasable RISC-V core both counts and samples, so ch28 (profiling) and ch29 (vectors) would have been unmeasurable, on boards that are hard to buy. | Part V moved to AArch64; the evidence and the cost are recorded in `hardware/README.md` and PLAN §5, and the five hardware-dependent chapters say what they assume in their own headers. |
| 2026-09-17 | the trap chapter, `sysfs/bare/trap.c`, `sysfs/bare/syscall.c` | The chapter said the compiler could save the handler's registers "because it can see both sides" — the handler and the interrupted code compiled together — and that a caller it had never seen would defeat it. GCC's `interrupt` attribute never looks at the interrupted code: it saves whatever the handler touches and restores it unchanged. The system-call chapter's handler is written by hand because a system call has to *read* the caller's registers and *change* one, and the compiler's saved copies are not somewhere its C can reach. | The paragraph and the two source comments say that instead; both results were re-captured, with no change to any observed value. |

When a measurement is corrected, the result file is regenerated and the fragment re-rendered in
the same commit, so the site and the PDF cannot disagree with this table.

## Known gaps

These are stated in the chapters that have them as well; this is the index.

| What | Where | Why, and what would close it |
|---|---|---|
| Specifications are cited without a revision | `references.bib` | The entries name the specification and its publisher but pin no revision, because none of the current content depends on a version-specific detail. Any chapter that comes to depend on one must pin the revision it consulted in the citation itself. |
| Board setup steps are generic | the board chapter | Flashing and boot-source selection depend on the image released at the time. The chapter gives the shape of the task and the generic commands and delegates the specifics to the vendor's quick-start, deliberately — a procedure the author cannot re-verify on every image is one that would rot silently. |
| Vendor documentation URLs | `references.bib` (`starfive-jh7110`, `sifive-u74`, `rpi-bcm2712`, `arm-a76-trm`) | Vendor documentation portals are reorganised. Check each against the copy actually consulted when the chapter citing it is written, and record the document title and date rather than relying on the link. |

## Reporting

Open an issue at <https://github.com/snowch/computer-systems/issues>. A correction to a *number*
is the most valuable kind: every figure names the result file and the code hash that produced it,
so a disagreement can be traced to a specific run rather than argued about.
