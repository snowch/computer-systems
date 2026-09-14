---
title: "The Memory Hierarchy [DRAFT]"
short_title: "ch15 The Memory Hierarchy"
---

(ch15)=
# ch15 · The Memory Hierarchy [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — Linux on real hardware, natively ([hardware](#ch00)) |
| **Prerequisites** | [ch14](#ch14) |
| **What it measures** | Latency against working-set size and against stride; measured cache and line sizes against the vendor's figures; TLB reach. |
| **Answers the cost of** | [ch02](#ch02), [ch07](#ch07) |
| **Assumes** | a particular cache hierarchy — the levels, sizes, line size and TLB reach are this core's. The method transfers to any machine; the numbers do not, and measuring your own is the exercise. |
:::

## The question

Where is the data, and what does each extra step out cost?

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

[To write: each problem is a stub under `tests/ch15/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
