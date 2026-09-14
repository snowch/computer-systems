---
title: "The Same Program on Both Targets [DRAFT]"
short_title: "ch13 The Same Program on Both Targets"
---

(ch13)=
# ch13 · The Same Program on Both Targets [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `xv6` and `host` — every example says which |
| **Prerequisites** | [ch12](#ch12) |
| **What it measures** | The same structural facts from both targets, and the first side-by-side timing: the board's, against QEMU's meaningless equivalent, shown deliberately. |
| **Answers the cost of** | [ch04](#ch04), [ch06](#ch06), [ch07](#ch07) |
:::

## The question

What does watching a program in a debugger fail to tell me about what it costs?

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

[To write: each problem is a stub under `tests/ch13/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
