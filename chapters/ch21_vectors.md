---
title: "Vectors [DRAFT]"
short_title: "ch21 Vectors"
---

(ch21)=
# ch21 · Vectors [DRAFT]

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Target** | `host` — Linux on real hardware, natively ([hardware](#ch00)) |
| **Prerequisites** | [ch20](#ch20) |
| **What it measures** | Speedup per loop with and without vectorisation, the emitted code that explains each, and one loop the compiler refuses — measured against the arithmetic bound, not celebrated alone. |
| **Assumes** | a vector unit — NEON on the reference core. This chapter became measurable when Part III moved to AArch64; on a RISC-V board without RVV 1.0 it reverts to reasoning about code the compiler emits but the hardware cannot run. |
:::

## The question

What does vectorising actually buy, and when will the compiler do it for me?

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

[To write: each problem is a stub under `tests/ch21/` with a test that passes only when
it is solved. There is no answer key — the test is the answer key, and it cannot be wrong about
whether it passes.]

## Where to go next

[To write: primary sources via `@citekey` against `references.bib`. Textbooks may appear here as
further reading and nowhere else — never as a source for this chapter's content (CLAUDE.md §5).]
