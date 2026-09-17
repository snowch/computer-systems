# Next steps

What is left, in the order it is worth doing, with the commands. Written after a page-by-page
review of all forty-seven pages (PR #25), which fixed what it found and left three jobs behind.

`PLAN.md` §11 is the milestone table and stays the roadmap. This file is the working list.

---

## 1. The board — everything here needs the Pi 5

This is M1, and it is **done (2026-09-16)**: the reference Pi 5 is set up, all twenty `host` figures
are measured and no longer pending, Appendix C is generated from the board, and the Wi-Fi
interference claim ch01 flagged is now measured in ch24. First contact with the hardware corrected
several chapters (below). Nothing here still needs the board. The procedure that follows is kept as
the record of how it was done and how to re-run it.

### What first contact changed

- **ch30 (profiling)** — `bench/board.py` called `perf record --call-graph none`, which perf 6.18
  rejects (it takes `fp|dwarf|lbr`); changed to `--no-call-graph`. Unblocked profile and skid.
- **ch28 (false sharing)** — the effect is a stable ~2.2× at two threads and ~1.5× at four, not the
  "several times" the prose claimed. The prose and the runner's 1.5× floor were corrected to match,
  and the surprise that it *shrinks* as cores are added is now in the text.
- **ch24 (measurement bias)** — the stack-placement experiment does not reproduce on the A76: the
  buffer genuinely moves (three different addresses) and the median does not change by a nanosecond.
  The workload was rebuilt into a real placement test that reports where the data landed, the guard
  now checks that placement moved rather than demanding an effect, and the chapter was reframed
  honestly — the method transfers, the 2009 magnitude does not. ch24's spread claim ("a multiple of
  the fastest") was also corrected to the measured tight-body-plus-interference-tail shape.

### Set it up

[ch01](chapters/setting_up_the_board.md) is the procedure and
[Appendix H](appendices/appendix_h_choosing_the_machine.md) is the shopping. The two things that
are not optional: the active cooler, because a board that throttles mid-run is measuring two
machines, and a wired link, because a radio's driver takes interrupts on the cores being measured.

```bash
python3 scripts/verify-setup.py        # on the board, over SSH
```

It must report `target host: ready`, and `perf` must both **count** and **sample** — those are
separate capabilities and a machine can have the first without the second. The reference board's
own counters went missing for a kernel release (@rpi-pmu-dt-6507), so verify rather than assume.

### Take `setup-host` first

```bash
python3 -m bench.run_setup --target host
```

That one result fills `setting-up-the-board-report`, which is the only pending figure a reader
meets before Part V. Commit it on its own — it is the board's account of itself and it is worth
being able to point at before anything else lands.

### Then the rest

```bash
make bench-board                       # refuses to run anywhere but the board
python3 scripts/render-figures.py
git add bench/results chapters/_generated && git commit
```

That runs ten runners and fills **twenty pending figures** across seven chapters:

| Result | Runner | Fills |
|---|---|---|
| `setup-host` | `bench.run_setup` | ch01's report |
| `measuring-host` | `bench.run_measuring` | ch24's clock, spread and bias |
| `hierarchy-host` | `bench.run_hierarchy` | ch25's levels, line, reach and vendor comparison |
| `bridge-host` | `bench.run_bridgecost` | ch23's cost |
| `loops-host` | `bench.run_loopcost` | ch26's cost |
| `pipeline-host` | `bench.run_pipelinecost` | ch27's ILP and branches |
| `vectors-host` | `bench.run_vectorcost` | ch31's speedup |
| `sharing-host` | `bench.run_sharingcost` | ch28's sharing and atomics |
| `oscost-host`, `faultcost-host`, `vdso-host` | `bench.run_oscost` | ch29's three tables |
| `profile-host`, `skid-host` | `bench.run_profilecost` | ch30's profiles and skid |

Every runner has a `--check` mode that re-runs and compares without writing. Use it once before
committing: a figure that moves between two runs of the same workload is telling you about the
machine's state rather than about the workload, which is ch24's whole subject.

### Appendix C — done

[appendices/appendix_c_perf_events.md](appendices/appendix_c_perf_events.md) is written and no longer
a stub. It is generated from the board by `bench/run_perfevents.py` (result `perfevents-host`): the
`armv8_cortex_a76` PMU, its seven counters, forty raw events, perf's portable aliases and the kernel
software events — and the counted-vs-computed distinction made concrete, since only seven events
count at once before perf multiplexes and scales the rest. Meanings cite the Cortex-A76 manual; the
inventory is the board's. That was the last piece that needed the hardware.

### Read the prose against the numbers when they land

Several chapters describe the *shape* of a result the board has not produced yet. They are written
so they read correctly either way, but the board is the first chance to check:

- ch28 says one arrangement is "several times slower than the other" — false sharing, unmeasured.
- ch24 says "the slowest run is a multiple of the fastest" — **checked**, the table agrees.
- ch25 says the latency curve is "flat, then steps, then flat, then steps again" — **checked**,
  and two sentences that did not survive the numbers were rewritten (the TLB "runs out first" and
  the stride curve "keeps climbing"). Two things the board should be asked again about:
  - the levels curve never rises above a few nanoseconds per dependent load out to the largest
    working set tried, which is far below any main-memory latency — either the set is still
    smaller than the last cache, or the chase is not defeating the prefetcher, or the loads are
    not dependent; a chase that reaches memory should step again, and this one does not;
  - the stride curve is not monotonic — it peaks around a page and falls back at larger
    strides — and the chapter now says it cannot explain that rather than pretending to.
- ch29 says the vDSO difference is large enough to matter — **checked**, the table agrees, and
  the chapter now reads the rows rather than only introducing them.

If a number comes back and contradicts one of those, the prose is what changes. That is invariant
3 working as intended rather than a defect, but it needs a pass.

Three more the editorial pass over Part V turned up, each needing the board rather than a laptop:

- **Two of the book's own tables price the same call differently.** The measurement chapter's
  clock table reports the cost of reading the clock; the OS-cost chapter's vDSO table reports
  `clock_gettime` through the vDSO, and `sysfs_now_ns` is a thin wrapper round exactly that call.
  The two figures differ by about a factor of two. Probably the harnesses: one takes the minimum
  of back-to-back differences, the other a per-call figure from a loop. Neither chapter mentions
  the other, and one of them should — decide which figure answers "what does reading the clock
  cost" and say so where the other is printed.
- **The profiling chapter has no duration.** Its before-and-after table is shares of samples, so
  it cannot say whether the partitioned arrangement is faster; the chapter now says so plainly
  rather than implying an outcome. A `tally` timing taken the measurement chapter's way, before
  and after, would close it and is a small addition to `bench/run_profile.py`.
- **The vectors chapter's float sum widened and bought nothing** (measured speedup of one under
  `-ffast-math`). That is a genuinely good finding and the chapter now leads with it, but it would
  be worth confirming it is not an artefact of the harness — if the loop is memory-bound at that
  size, a smaller working set should show the widening paying.

---

## 2. Chapter numbers in code comments — 535 of them, and they are stale

**This does not need the board.** Every runner except the ten above works off-board; the
listings, the bare-metal results and the xv6 censuses all regenerate under QEMU on a laptop.

> **Status (2026-09-16).** The reader-facing and kernel-shipped trees are done: every `chNN` and
> `chapter N` under `sysfs/`, `xv6/patches/` and `xv6/apps/` is now a topic name, judged by which
> chapter owns each source (via `bench/figures.py` and the chapter `literalinclude`s), not by the
> printed number. `tests/test_book.py::test_no_shipped_source_names_a_chapter_by_number` guards all
> three trees so it cannot come back. The fingerprints those edits invalidated are handled two ways:
> the 47 deterministic results (listings, bare, xv6 censuses, host listings and artefacts)
> regenerate on `ubuntu-24.04` through `.github/workflows/regen.yml` on any `regen/**` branch; the 15
> `host/measurement` board timings, which a comment cannot have changed, are re-stamped in place by
> `scripts/restamp-host-fingerprints.py` (no re-measure).
>
> **Status (2026-09-17). Done.** `bench/`, `scripts/` and `tests/` are named rather than numbered
> too. Thirty runners opened by naming the wrong chapter, and four of those strings were not
> comments — they were the `note` and `for` fields a runner stamps into its result, so appendix D
> printed "the process calls, including the one ch13's workload uses" to the reader, where ch13 is
> *Representing Information*. `bench/measure.py` was included despite being `CORE_SOURCES`, since
> the regeneration was happening anyway. Two more guards:
> `test_no_runner_names_a_chapter_by_number` over every `bench/*.py` but `outline.py`, where the
> numbers are derived and `ch` is meant, and `test_no_committed_result_names_a_chapter_by_number`
> over `bench/results/`. `tests/test_book.py` is deliberately outside both: most of its `chNN` are
> quotations of the bug each guard was written for, and correcting those would make the record
> false.
>
> **Optional polish, still open:** the patch **filenames** are old chapter numbers
> (`13-trap-census.patch` is the traps chapter's, off by three); renaming them to a plain `01`–`06`
> sequence also touches the `PATCH=` constants in six `bench/run_*.py`, three `{literalinclude}`
> paths in the traps, page-faults and file-system chapters, and `xv6/README.md`. And
> `tests/prerequisites_and_setup/ch00ping.c` is a chapter number in a filename — correct today,
> which is exactly why it is easy to leave.

### What is wrong

The rule in CLAUDE.md — *a chapter's number is never an identifier* — was applied to the book's
markdown and never to its code. `scripts/sync-labels.py` scans `index.md`, `PLAN.md`,
`ORIGINALITY.md`, `CHECKPOINTS.md`, `chapters/` and `appendices/`. It has never looked at a `.c`
file, and a bare `chNN` in a comment has no anchor to derive a number from anyway.

Every one checked so far is wrong, by a consistent offset per era:

```
!! trap.c        header says ch04   the chapter that runs it is ch06
!! privilege.c   header says ch05   ch07
!! paging.c      header says ch06   ch08
!! harts.c       header says ch06   ch08
!! syscall.c     header says ch07   ch09
!! descriptors.c header says ch08   ch10
!! fork.c        header says ch09   ch11
!! elfdump.c     says "ch12 takes a binary apart"   ch15
!! tally.c       says "the program chapter 20 profiles"   ch30
```

Two are reader-visible:

- **`./run --list`** prints each program's header comment, and ch00 tells the reader to run it.
  Five of the strings name a chapter, and all five are wrong.
- **`case C('T'): // Print the trap census (Systems From Scratch, ch13).`** is in five patches and
  lands in `console.c` in the kernel a reader builds. ch13 is *Representing Information*, which
  has nothing to do with a trap census.

The patch **filenames** are old chapter numbers too — `13-trap-census.patch` is ch16's,
`14-pagetable-census.patch` is ch17's, and so on, all off by three. `xv6/patches/README.md` says
the prefix exists "so `git apply` order matches chapter order", which a plain sequence satisfies
without claiming anything that can go stale.

### Where they are

```
  205  tests/          conftests, stubs and problem docstrings
  149  bench/          runner docstrings and messages
   54  xv6/patches/    comments that ship inside the kernel
   41  scripts/        ci-check.sh section headings, mostly
   38  sysfs/lib + include/
   22  sysfs/bare/     every program's header
   11  sysfs/tools/
    8  xv6/apps/
    7  sysfs/bench/
  535  total, across 190 files
```

Not all of them are wrong — `tests/prerequisites_and_setup/` legitimately says ch00 — but the
ones spot-checked outside that directory all were.

### Suggested approach

**Do not renumber them.** The same drift recurs at the next insertion, and there is no mechanical
fix: the existing numbers are wrong, so rewriting `chNN` to a link would cement the errors. Each
one has to be read.

The fix CLAUDE.md applies to itself is *prefer the name*. `ch04's handler` becomes `the bare-metal
trap chapter's handler`, or the chapter's title. A name cannot go stale and needs no syncer.

Order:

1. `sysfs/bare/*.c` headers and `sysfs/tools/*.c` headers — nine files, reader-visible through
   `./run --list`. Regenerate afterwards: `python3 -m bench.run_bare` (seven results) and the
   listing runners.
2. `xv6/patches/*.patch` — rename the prefixes to a plain sequence `01`–`06`, fix the `ch13`
   comment in all five (it appears as an added line in one and as context in four, so they have
   to change together), update the `PATCH =` constants in `bench/run_*.py`, the three
   `{literalinclude}` paths in ch16, ch18 and ch19, and `xv6/README.md`'s recipe. Then regenerate:
   `python3 -m bench.run_traps`, `run_pagetable`, `run_faults`, `run_interrupts`, `run_switch`,
   `run_blocks` — all six boot xv6 under QEMU and take about a minute each.
3. `bench/`, `scripts/` and `tests/` — no fingerprints involved, so purely a reading job.

Then a guard: no `chNN` under `sysfs/`, `xv6/patches/` or `xv6/apps/`. `tests/test_book.py` has
eleven checks from the review to copy the shape from — each one names the bug it was written for
in its docstring, which is the house style.

**Watch the fingerprints.** A result names its sources and hashes them, so editing a comment in a
file a result names invalidates it. `python3 scripts/verify-numbers.py` says which. All of the
affected ones regenerate locally; none of them needs the board.

---

## 3. PLAN.md's per-chapter entries

The structural claims are fixed — the outline's opening counts, the missing appendices G and H,
the targets table that described two targets in a book that has had three since Part II. The
per-chapter entries themselves are current and were regenerated.

**Done (2026-09-16), in PR #28.** Every `chNN` in the per-chapter entries is now either a
`[chNN](#anchor)` link — which `sync-labels.py` scans PLAN.md for and keeps correct — or a
`#### chNN ·` heading keyed by the frozen label. The two real errors this section flagged are
fixed: the Part I preamble now links bit manipulation to `[ch13]`, page-table encoding to `[ch17]`,
the preprocessor to `[ch12]` and the system-call path to `[ch16]`; the Part V mapping table reads
`[ch27] The CPU` and `[ch29] The OS Layer's Cost`, not ch27 twice. `sync-labels.py --check` passes.

---

## 4. Four citations need a browser

**Done (2026-09-16).** All four fetched and confirmed to resolve to the right resource, and
`references.bib` carries the current URL for each.

| Key | URL in `references.bib` | Resolves to |
|---|---|---|
| `xv6-book` | `https://pdos.csail.mit.edu/6.1810/` | MIT 6.1810 (the live course number; 6.828 was the old one) |
| `gregg-sysperf` | `https://www.brendangregg.com/systems-performance-2nd-edition-book.html` | Gregg, *Systems Performance* 2nd ed. |
| `elf-abi` | `https://www.sco.com/developers/gabi/` | System V gABI (the ELF chapters) |
| `mytkowicz2009wrong` | `doi:10.1145/1508244.1508275` | resolves via doi.org to the ACM entry for the ASPLOS'09 paper |

---

## 4a. The social-share image is a random chapter diagram

Noticed while fixing the site icon, and left alone deliberately because it is a different job.

The published pages carry `<meta property="og:image" content=".../prerequisites-and-se-….svg">`.
Nobody chose that: MyST falls back to the first image it finds in the project when
`project.thumbnail` is unset, and the first image is a diagram from the setup chapter. So every
link to this book — Slack, iMessage, a forum — previews with an SVG of a QEMU boot diagram, and
most platforms decline to render SVG at all and show nothing.

`project.thumbnail` in `myst.yml` is the fix and is one line. What it should point at is the
question: a proper card is 1200×630 with the title set in it, which is a design task rather than
a path. `icons/icon-512.png` would do as a stopgap — deliberate and branded, if the wrong shape.

---

## 5. Editorial calls that are yours, not a bug

Found during the review, deliberately not changed.

**Exact figures repeated from a table into prose.** Invariant 2 says no numbers typed into prose,
and these are accurate today but would go stale silently:

- ch15 — "Eighteen sections, two segments."
- ch16 — "the way in saves thirty-one registers"
- ch20 — "Everything else in those twenty-five instructions"
- ch21 — "the fourteen against thirty-one above"

Each is a good sentence and each duplicates a number from the table directly above it. The line
drawn during the review was that a hedge ("eighty-odd", "thirty-odd") is the book's idiom and an
exact repetition is the risk, but it is a judgement and all four are worth a decision.

**Four of Part II's six chapters open *What we measured* with the same sentence, verbatim.** A
refrain, but an uneven one — two chapters do not join in.

**`tests/prerequisites_and_setup/ch00ping.c`** has a chapter number in a filename. It is correct
today, which is exactly why it is easy to leave.

---

## Running the checks

```bash
make check                              # ./scripts/ci-check.sh — what CI runs
python3 -m pytest tests/ -q -m "not problem"
python3 scripts/sync-labels.py --check
python3 scripts/verify-numbers.py
python3 scripts/render-figures.py --check
```

`make check` was green at the end of the review.
