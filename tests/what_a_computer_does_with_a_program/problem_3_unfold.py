"""Problem 3 of the whole-program chapter — take the folding away.

`sysfs_sum_folded` counts to sixty-four and the compiler emits no loop at all: it ran the loop
itself and wrote down the answer. Your job is to write a function that computes the same number
and that the compiler *cannot* do this to.

The rule: it must still return the same value, it must still contain a loop in the source, and
the machine must actually execute that loop. The test disassembles what the compiler emitted and
checks for a backward branch — so you cannot pass by returning a constant, and you cannot pass by
writing something the optimiser can see through.

There is more than one way to do it, and they are not equally good. The whole-program chapter explains what the
compiler has to be able to prove before it may fold a loop; take that away and the folding goes.
"""

from __future__ import annotations

#: The body of a C function, compiled by the test exactly as written here.
#:
#: Keep the signature. Everything between the braces is yours.
UNFOLDABLE_SUM = """
unsigned long reader_sum(unsigned long span) {
  /* Problem 1.3 — see the Problems section of the whole-program chapter.
   *
   * Return the sum of every integer below `span`, using a loop the compiler leaves alone. */
  return 0;
}
"""
