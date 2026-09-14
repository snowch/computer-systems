"""Disassembly as a stamped artefact.

Chapters 4, 16 and 17 are about reading machine code, so they have to show some. The book's rule
is that nothing is pasted into prose (CLAUDE.md), and a listing pasted from somebody's terminal is
the worst kind of pasted thing: it looks authoritative, it is unverifiable, and it silently stops
matching the compiler the moment either changes.

So a listing is treated exactly like a measurement. A runner produces it, the result records the
toolchain and flags that produced it, a fragment is rendered from that result, and CI fails when
the two disagree. The difference from a timing is a happy one: **a listing is reproducible in
CI**, because it depends on the compiler rather than on the machine. CI can therefore regenerate
it and diff, instead of taking the committed copy on trust — which is why ``bench/run_disasm.py
--check`` runs on every push and ``make bench-board`` does not.

Four decisions, each of which was a wrong answer first.

**Object files, not executables.** Disassembling a linked binary bakes in addresses that move
whenever anything ahead of the function changes, so a listing would churn for reasons having
nothing to do with the code. An object file starts its text section at zero, and the offsets that
remain are the ones worth reading.

**objdump picks the function, not us.** ``--disassemble=SYMBOL`` uses the symbol's size from the
ELF symbol table, which is the only thing that actually knows where a function ends. Scanning for
the next ``<name>:`` header instead looks equivalent and is not: the RISC-V toolchain keeps
assembler-local labels — ``.L4``, ``.L6`` — in the object file's symbol table so the linker can
relax branches against them, so objdump prints them as headers *inside* a function, and a scan
stops at the first one. On AArch64 they are absent and the same code works. That is a nasty shape
of bug: correct on the architecture you tested, truncating listings on the other.

**Compiled without ``-g``.** Debug info emits view labels (``.LVL3``, ``.LBE2``) which, on RISC-V
and for the same relaxation reason, also reach the symbol table and get printed as headers. They
split an eight-instruction function across six of them and say nothing about the code. Dropping
``-g`` changes no instruction; the stamp records the exact flags used, so the command in the
caption reproduces the listing in the book byte for byte, which is the property that matters.

**No normalisation beyond that.** What objdump prints for the function is what the chapter shows,
annotations and all. The temptation is to tidy — strip the comment column, renumber the labels —
and every bit of that puts the book one step further from what the reader sees on their own
screen. The local labels that survive on RISC-V stay in the listing: they are a real difference
between the two toolchains, and a chapter can say so.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bench.measure import HostTarget, compile_program
from bench.stamp import ROOT, compiler_version, flags_string

#: A symbol header in objdump's output: ``0000000000000000 <name>:``.
_SYMBOL = re.compile(r"^[0-9a-f]+ <([^>]+)>:$")

#: ``…: file format elf64-littleaarch64`` — objdump's own account of what it is reading, which
#: beats parsing an architecture out of a target name.
_FORMAT = re.compile(r"file format \S+?(aarch64|riscv|arm|x86-64|i386)\b")

#: An instruction line: offset, tab, mnemonic.
_INSTRUCTION = re.compile(r"^\s+[0-9a-f]+:\t")

#: Flags that say nothing about the instructions in an object file, and are dropped before
#: compiling one. ``-static`` is a link option and ``-c`` never reaches the linker; ``-g`` emits
#: debug info, which on RISC-V reaches the symbol table and litters the listing with view labels.
#: Both are dropped from the recorded flags too, so the caption shows a command that reproduces
#: what the book prints.
NOT_CODE_GENERATION = frozenset({"-static", "-g", "-ggdb", "-g3"})


class SymbolNotFoundError(LookupError):
    """The function the chapter wants to show is not in the object file.

    Usually one of three things: the name is misspelled, it was inlined away at this optimisation
    level, or it is ``static`` and the compiler discarded it because nothing in this translation
    unit calls it. All three are worth failing loudly for, because the alternative is a chapter
    with an empty listing in it.
    """


@dataclass(frozen=True)
class Listing:
    """One function's disassembly, and how it was produced."""

    symbol: str
    text: str
    arch: str
    toolchain: dict[str, Any]

    @property
    def instructions(self) -> int:
        """How many instructions the compiler emitted, for a chapter that counts them."""
        return sum(1 for line in self.text.splitlines() if _INSTRUCTION.match(line))

    def as_summary(self) -> dict[str, Any]:
        """The shape this takes inside a result's ``summary``."""
        return {"symbol": self.symbol, "text": self.text, "instructions": self.instructions}


def objdump_for(cc: str) -> str:
    """The objdump that matches a compiler.

    ``aarch64-linux-gnu-gcc`` implies ``aarch64-linux-gnu-objdump``; a bare ``gcc`` or ``cc``
    implies the system one. A mismatched objdump mostly works and then silently mis-decodes the
    instructions that matter, which is a memorable afternoon.
    """
    if cc.endswith("-gcc"):
        candidate = cc[: -len("gcc")] + "objdump"
        if shutil.which(candidate):
            return candidate
    for candidate in ("objdump", "llvm-objdump"):
        if shutil.which(candidate):
            return candidate
    raise FileNotFoundError(f"no objdump to match {cc}")


def code_flags(flags: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """The flags that affect the instructions, which are the ones worth recording for a listing."""
    return tuple(flag for flag in flags if flag not in NOT_CODE_GENERATION)


def symbols(dump: str) -> list[str]:
    """Every symbol objdump printed a header for, in the order it printed them."""
    return [m.group(1) for m in map(_SYMBOL.match, dump.splitlines()) if m]


def extract(dump: str, symbol: str) -> str:
    """Drop objdump's preamble and return the function it disassembled.

    The preamble names the object file by path, so it cannot go into the book: it would differ
    between a laptop, CI and the board while nothing had changed. Everything from the symbol's own
    header onwards is kept verbatim.

    This assumes ``--disassemble=SYMBOL`` did the selecting, so it deliberately does *not* try to
    find where the function ends. See the module docstring for why doing that by hand is wrong.
    """
    lines = dump.splitlines()
    for index, line in enumerate(lines):
        match = _SYMBOL.match(line)
        if match and match.group(1) == symbol:
            return "\n".join(lines[index:]).rstrip()

    present = sorted(set(symbols(dump)))
    raise SymbolNotFoundError(
        f"{symbol!r} is not in this object file. It may have been inlined, or discarded as an "
        f"uncalled static. Symbols present: {', '.join(present) or 'none'}"
    )


def architecture(dump: str) -> str:
    """What objdump says it is reading, normalised to the names the book uses."""
    match = _FORMAT.search(dump)
    if not match:
        raise ValueError(f"objdump did not name a file format:\n{dump[:200]}")
    return "riscv64" if match.group(1) == "riscv" else match.group(1)


def disassemble(
    sources: list[str],
    symbol: str,
    target: HostTarget,
    *,
    includes: list[str] | None = None,
    build_dir: Path | None = None,
) -> Listing:
    """Compile to an object file and return one function's disassembly, with its provenance."""
    flags = code_flags(target.flags)
    build = build_dir or (ROOT / "sysfs" / "build")
    output = build / f"{Path(sources[0]).stem}-{architecture_of(target)}.o"
    built = compile_program(
        sources,
        output,
        HostTarget(name=target.name, cc=target.cc, flags=flags),
        extra_flags=["-c"],
        includes=includes or ["sysfs/include"],
    )

    tool = objdump_for(target.cc)
    command = [tool, "-d", "--no-show-raw-insn", f"--disassemble={symbol}", str(built.path)]
    dump = subprocess.run(command, capture_output=True, text=True, check=True).stdout

    try:
        text = extract(dump, symbol)
    except SymbolNotFoundError:
        # A name objdump does not recognise produces a dump with no symbols in it at all, so the
        # error would list nothing. Ask again for the whole object file, purely so the message can
        # say what *is* there — which is the sentence that actually shortens the debugging.
        whole = subprocess.run(
            [tool, "-d", "--no-show-raw-insn", str(built.path)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        raise SymbolNotFoundError(
            f"{symbol!r} is not in {output.name}. It may have been inlined, or discarded as an "
            f"uncalled static. Symbols present: {', '.join(sorted(set(symbols(whole)))) or 'none'}"
        ) from None

    return Listing(
        symbol=symbol,
        text=text,
        arch=architecture(dump),
        toolchain={
            "cc": compiler_version(target.cc),
            "flags": flags_string((*flags, "-c")),
            "objdump": f"{tool} -d --no-show-raw-insn --disassemble={symbol}",
        },
    )


def architecture_of(target: HostTarget) -> str:
    """The architecture a target builds for, from its name.

    Only used to name a build artefact. The architecture that reaches a *result* comes from
    objdump, which read the ELF header rather than a naming convention.
    """
    for part in target.name.split("-"):
        if part in {"aarch64", "riscv64"}:
            return part
    return "other"
