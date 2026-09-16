---
title: "Appendix A — RISC-V Registers and CSRs"
short_title: "Appendix A"
---

(appendix-a)=
# Appendix A · RISC-V Registers and CSRs

An appendix in this book is a reference, not a chapter: no argument, no narrative, and everything
in it either cites a primary source or comes from a stamped result under `bench/results/`.

Everything on this page is from the RISC-V unprivileged @riscv-isa-unprivileged and privileged
@riscv-isa-privileged specifications and the psABI @riscv-psabi, restated for the subset this book
uses. It is not a substitute for reading them; it is what to have open while you do.

## The integer registers

Thirty-two, each sixty-four bits wide on RV64. `x0` is hardwired to zero — writes to it are
discarded, which is how the instruction set gets a no-op, a move and a compare-against-zero
without spending encodings on them.

The names on the left are the only ones you will see in this book's listings. The hardware has no
opinion about them: the roles below are a *convention* @riscv-psabi, agreed between compilers, and
the point [ch14](#machine-level-code-on-riscv) makes is that a convention is a contract and an interrupt is not a party
to it.

| Register | `x` number | Role | Preserved across a call? |
|---|---|---|---|
| `zero` | `x0` | Hardwired zero | — |
| `ra` | `x1` | Return address | No |
| `sp` | `x2` | Stack pointer | Yes |
| `gp` | `x3` | Global pointer | — (set once) |
| `tp` | `x4` | Thread pointer | — (set once) |
| `t0`–`t2` | `x5`–`x7` | Temporaries | No |
| `s0`/`fp` | `x8` | Saved, or frame pointer | Yes |
| `s1` | `x9` | Saved | Yes |
| `a0`–`a1` | `x10`–`x11` | Arguments, and return values | No |
| `a2`–`a7` | `x12`–`x17` | Arguments | No |
| `s2`–`s11` | `x18`–`x27` | Saved | Yes |
| `t3`–`t6` | `x28`–`x31` | Temporaries | No |

Two things worth carrying:

**Eight argument registers.** A call passing eight or fewer word-sized arguments touches no memory
to do it, which is most of why [ch14](#machine-level-code-on-riscv)'s `-O2` listings have no stack frame at all.

**"Preserved" means the callee promised.** A caller-saved register is not saved by anybody unless
the caller needs it afterwards; a callee-saved one is saved by whoever wants to use it. Neither
promise binds the hardware, which is why [ch16](#traps-and-system-calls)'s trap path saves all thirty-one.

## The control and status registers this book touches

CSRs are a separate address space, read and written with their own instructions (`csrr`, `csrw`,
`csrrw` and the immediate forms). They are not the integer registers and they are not memory.

The privileged specification @riscv-isa-privileged defines several dozen. These are the ones the
kernel in this book reads or writes, each with the chapter that meets it.

| CSR | What it is | Where |
|---|---|---|
| `stvec` | The address the hardware jumps to on a supervisor trap | [ch16](#traps-and-system-calls) |
| `sepc` | The PC at the moment of the trap; `sret` returns here | [ch16](#traps-and-system-calls) |
| `scause` | Why the trap happened, as a code with the interrupt bit at the top | [ch16](#traps-and-system-calls), [ch19](#interrupts-and-drivers) |
| `sstatus` | Supervisor status: previous privilege, previous interrupt-enable | [ch16](#traps-and-system-calls), [ch19](#interrupts-and-drivers) |
| `sscratch` | One word the trap path may use before it has a usable register | [ch16](#traps-and-system-calls) |
| `stval` | The faulting address, for a fault that has one | [ch18](#page-faults-as-a-feature) |
| `satp` | The root page table and the translation mode | [ch17](#virtual-memory) |
| `sie` / `sip` | Which interrupts are enabled, and which are pending | [ch19](#interrupts-and-drivers) |
| `time` | The real-time counter, readable from user mode | [ch19](#interrupts-and-drivers) |

**`scause`'s top bit is the one to read first.** It separates an interrupt — something outside the
program asking for attention — from an exception, which is this instruction refusing to complete.
The rest of the field means different things in the two cases, and [ch19](#interrupts-and-drivers) is about why the
distinction is structural rather than a numbering convenience.

**`sscratch` exists because of a bootstrapping problem.** A trap handler needs a register to work
with and every register currently belongs to the interrupted program. `sscratch` is the one place
to put something that survives the swap, and [ch16](#traps-and-system-calls) traces exactly what xv6 keeps there.

## Sv39, in one place

The paging scheme this book uses. [ch17](#virtual-memory) derives it and measures the walk; this is the
field layout to keep beside that chapter.

A virtual address is thirty-nine bits of meaning: three nine-bit indices and a twelve-bit offset.
A page-table entry is sixty-four bits: flags at the bottom, a physical page number above them.

| Field | Bits | What it decides |
|---|---|---|
| `V` | 0 | Whether the entry means anything at all |
| `R` `W` `X` | 1–3 | Readable, writable, executable. All three clear means "this points at another table" |
| `U` | 4 | Reachable from user mode |
| `G` | 5 | Global — the same in every address space |
| `A` `D` | 6–7 | Accessed, dirty |
| `RSW` | 8–9 | Two bits the hardware ignores and software may use |
| `PPN` | 10–53 | The physical page number |

**The `R`/`W`/`X` trick is the one to remember.** An entry with none of them set is a pointer to
the next level; an entry with any of them set is a leaf. That is how one format serves both, and
how a leaf can appear at a level above the last to map a larger page.

## Where to go next

The unprivileged specification @riscv-isa-unprivileged for the instruction encodings and the
memory model, the privileged specification @riscv-isa-privileged for everything on this page below
the register table, and the psABI @riscv-psabi for the convention. The SBI specification
@riscv-sbi describes the layer beneath the kernel that [ch16](#traps-and-system-calls) mentions and this book does
not otherwise use.
