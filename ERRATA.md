# Errata and known gaps

Two lists. The first is for things that were **wrong** — including anywhere a later chapter
contradicts an earlier one, in which case the fix goes in the earlier chapter (CLAUDE.md §6). The
second is for things that are **not finished**, recorded so they are not mistaken for oversights.

## Corrections

| Date | Chapter | What was wrong | Fixed in |
|---|---|---|---|
| 2026-09-14 | ch00, PLAN §5 | Part III was planned on RISC-V hardware. No purchasable RISC-V core both counts and samples, so ch20 (profiling) and ch21 (vectors) would have been unmeasurable, on boards that are hard to buy. | Part III moved to AArch64; the evidence and the cost are recorded in `hardware/README.md` and PLAN §5, and the five hardware-dependent chapters say what they assume in their own headers. |

When a measurement is corrected, the result file is regenerated and the fragment re-rendered in
the same commit, so the site and the PDF cannot disagree with this table.

## Known gaps

These are stated in the chapters that have them as well; this is the index.

| What | Where | Why, and what would close it |
|---|---|---|
| The board has not reported | `ch00-board` figure, `bench/figures.py` | `bench/results/setup-host.json` does not exist yet. Run `make bench-board` on the VisionFive 2 Lite, commit the result, and remove the `pending=` marker. |
| Appendix C is empty | `appendices/appendix_c_perf_events.md` | The `perf` events this board has are a property of the board and its firmware, not something to look up. It is generated from the board once M1 lands (PLAN.md §11). |
| Specifications are cited without a revision | `references.bib` | The entries name the specification and its publisher but pin no revision, because none of the current content depends on a version-specific detail. Any chapter that comes to depend on one must pin the revision it consulted in the citation itself. |
| Vendor documentation URLs | `references.bib` (`starfive-jh7110`, `sifive-u74`) | Vendor documentation portals are reorganised. Check each against the copy actually consulted when the chapter citing it is written, and record the document title and date rather than relying on the link. |
| Board setup steps are generic | ch00, "Setting up the board" | Flashing and boot-source selection depend on the image released at the time. The chapter gives the shape of the task and the generic commands and delegates the specifics to the vendor's quick-start, deliberately — a procedure the author cannot re-verify on every image is one that would rot silently. |
| Chapters ch01–ch21 are stubs | `chapters/` | Each carries its target, question and prerequisites from `bench/outline.py`, and `[DRAFT]` in its title. PLAN.md §4 has what each owes. |

## Reporting

Open an issue at <https://github.com/snowch/computer-systems/issues>. A correction to a *number*
is the most valuable kind: every figure names the result file and the code hash that produced it,
so a disagreement can be traced to a specific run rather than argued about.
