---
title: "C Without a Runtime [DRAFT]"
short_title: "ch02 C Without a Runtime"
---

(ch02)=
# ch02 · C Without a Runtime [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` — the teaching kernel under QEMU |
| **Prerequisites** | [ch01](#ch01) |
| **What it measures** | What the kernel does not have, counted from the kernel as built: its stack size, its floating-point instructions, and how much of the C library it reimplements. |
:::

## The question

I already write C — which of my habits stop working in a kernel?

[To write: one paragraph. State the question this chapter answers and why the previous chapter
leaves it open. No summary of what is to come — the reader can see the headings.]

## The material

[To write: the body. Short sections. Code is quoted from the working tree with
`{literalinclude}` and text anchors, never pasted. See AUTHORING_GUIDE.md.]

## What we measured

[To write: `{include}` the generated fragments declared in `bench/figures.py`. No number is ever
typed here. For a `host` figure that still needs the board, declare it `pending=` and write the
prose so it reads correctly once the numbers land.]

## What this cannot tell you

[To write. **Mandatory.** What the target, the tooling or the hardware could not show, and what
you did instead. This chapter is not finished while this section is missing.]

## Problems

[To write: each problem is a stub under `tests/ch02/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
