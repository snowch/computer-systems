---
title: "The CPU [DRAFT]"
short_title: "ch17 The CPU"
---

(ch17)=
# ch17 · The CPU [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — Linux on real hardware, natively ([hardware](#ch00)) |
| **Prerequisites** | [ch16](#ch16) |
| **What it measures** | Misprediction rate against branch predictability; IPC against dependency-chain length; the cost of a mispredict, derived and stated as derived. |
| **Answers the cost of** | [ch04](#ch04) |
| **Assumes** | a specific microarchitecture. The reference is an out-of-order, 4-wide Cortex-A76; core width, branch predictor and PMU event names all differ elsewhere, and on an in-order core these experiments get easier to read, not harder. |
:::

## The question

What is this core doing between fetching an instruction and finishing it?

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

[To write: each problem is a stub under `tests/ch17/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
