---
title: "Interrupts, and Who Is Allowed To [DRAFT]"
short_title: "05 · Interrupts, and Who Is Allowed To"
---

(interrupts-and-privilege)=
# 05 · Interrupts, and Who Is Allowed To [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `bare` — the same machine under QEMU with no operating system on it |
| **Prerequisites** | [ch04](#a-trap-with-nothing-else) |
| **What it measures** | A timer interrupt taken with no kernel present, and an access refused because the program had dropped a privilege level. |
:::

## The question

What arrives without being asked for, and what does a privilege level actually restrict?

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

[To write: each problem is a stub under `tests/interrupts_and_privilege/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
