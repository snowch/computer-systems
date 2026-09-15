---
title: "Appendix D — An xv6 File Map"
short_title: "Appendix D"
---

(appendix-d)=
# Appendix D · An xv6 File Map

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

This one is walked from the submodule at its pinned commit rather than written, so every line
count here is one `wc -l` will agree with on the tree you have checked out — and a file renamed
upstream fails CI rather than quietly making this page wrong.

## How much kernel there is

```{include} ../chapters/_generated/appendix-d-size.md
```

That first figure is the reason this book uses xv6 at all. A production kernel is several million
lines and nobody reads it; this one is small enough that the files Part IV opens are most of it,
and the rest is not hidden from you — it is just not what any chapter needed.

## Which chapter reads which file

```{include} ../chapters/_generated/appendix-d-map.md
```

Keep this open from [ch13](#traps-and-system-calls) onwards. The rows are grouped by chapter because that is how you
will arrive here: a chapter is discussing something, and the question is which of forty-odd files
to open beside it.

## What is not in the table

Everything else in `kernel/` — headers describing on-disk and in-memory structures, the string and
printing routines, the linker script, the parts of the build no chapter discusses. They are not
listed individually because a list of them is a directory listing, which you already have.

Two absences are deliberate rather than incidental.

**`main.c` is not mapped to a chapter.** It is worth reading early and it belongs to no chapter in
particular: it is the order in which everything else is initialised, which is a useful thing to
have seen once and a poor thing to study in isolation.

**Nothing in `user/` is mapped either.** The book's own programs live in `xv6/apps/`, and the
kernel's user programs are read in passing rather than studied — with one exception the chapters
name, which is that [ch13](#traps-and-system-calls) explains why the shell is the worst possible thing to measure.

## What this cannot tell you

**Where a symbol is.** This maps files, not functions. `grep -rn` over `kernel/` answers that
question faster than any table could, and stays right when upstream moves something.

**What the file does.** The "For" column says what a chapter goes there *for*, which is narrower
on purpose. `fs.c` does a great deal that [ch19](#the-file-system) never mentions.

**Anything about a different xv6.** The commit is pinned and recorded in the conditions line under
each table. MIT's xv6 changes; a map of one version describing another is exactly the failure this
page is generated to avoid.
