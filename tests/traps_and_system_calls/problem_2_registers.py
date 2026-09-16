"""Problem 2 of the traps-and-system-calls chapter — which registers must the trap path save?

`uservec` saves a fixed set of registers into the trapframe before the kernel touches anything.
Work out which ones it *has* to save, then check yourself against what it actually does.

The reasoning is the same one the machine-code chapter used for a function's prologue, applied to a caller that
is not a function and did not agree to anything. A called function preserves the callee-saved
registers because the convention says so. **An interrupt is not a call**: user code did not ask to
be interrupted, made no arrangements, and must find every register exactly as it left it.

State how many general-purpose registers the machine has, how many the trap path must therefore
preserve, and why the answer is not simply all of them.
"""

from __future__ import annotations

#: How many general-purpose integer registers RV64 has, including the one hardwired to zero.
TOTAL_REGISTERS: int | None = None

#: How many of them `uservec` actually stores into the trapframe.
SAVED_BY_USERVEC: int | None = None

#: The names of the registers it does *not* need to store, and there is more than one reason a
#: register can end up on this list. The traps-and-system-calls chapter gives you two of them and the psABI gives the rest.
NOT_SAVED: tuple[str, ...] = ()
