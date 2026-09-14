---
title: "Appendix B — gdb for Kernels and RISC-V [DRAFT]"
short_title: "Appendix B"
---

(appendix-b)=
# Appendix B · gdb for Kernels and RISC-V [DRAFT]

:::{note} Not written yet
**What it will hold.** Attaching to QEMU, the xv6 workflow, watchpoints on physical memory, and what to do when the stack is nonsense.

**Where it comes from.** Procedures verified against the repository's own `make xv6-gdb`, so every sequence here is one that has been run. [ch00](#ch00) sets the debugger up; this is where the workflow lives.
:::

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

[To write: the reference itself. PLAN.md §4 has the scope.]
