---
title: "Memory Ordering on Real Hardware [DRAFT]"
short_title: "ch18 Memory Ordering on Real Hardware"
---

(ch18)=
# ch18 · Memory Ordering on Real Hardware [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — Linux on real hardware, natively ([hardware](#ch00)) |
| **Prerequisites** | [ch17](#ch17) |
| **What it measures** | [To write: the figure this chapter produces, and the result file under `bench/results/` it lands in.] |
| **Assumes** | four cores, and this interconnect's coherence behaviour. A different core count moves the scaling curve without changing the mechanism; two cores make the chapter thin. |
:::

## The question

What do four cores cost each other, and what does a fence actually buy?

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

[To write: each problem is a stub under `tests/ch18/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
