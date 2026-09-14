"""Disassembly is an artefact the book publishes, so it gets checked like one.

The one behaviour here worth a whole file is the truncation trap, and it is worth it because the
bug is invisible from one architecture. The RISC-V toolchain leaves assembler-local labels in the
object file's symbol table so the linker can relax branches against them, so objdump prints
``0000000000000018 <.L4>:`` *inside* a function. Anything that decides where a function ends by
scanning for the next symbol header stops there and publishes half a listing — while passing every
test on AArch64, where those labels are gone.
"""

from __future__ import annotations

import pytest

from bench.disasm import (
    Listing,
    SymbolNotFoundError,
    architecture,
    code_flags,
    disassemble,
    extract,
    objdump_for,
    symbols,
)
from bench.measure import flags_for
from bench.run_disasm import SOURCES, WORLD, capture, target_for
from bench.stamp import ROOT

SHAPES_SOURCE, _SHAPES_HEADER, SHAPES_SYMBOLS = SOURCES["shapes"]

#: Real output, from ``riscv64-linux-gnu-objdump -d --no-show-raw-insn --disassemble=sysfs_clamp``
#: on gcc 13.3's object file. Checked in as a fixture rather than generated, so that the trap it
#: describes is still tested on a machine with no RISC-V toolchain at all.
RISCV_DUMP = """
shapes-riscv64.o:     file format elf64-littleriscv


Disassembly of section .text:

0000000000000000 <sysfs_clamp>:
   0:\tblt\ta0,a1,18 <.L4>
   4:\tmv\ta1,a0
   6:\tblt\ta2,a0,10 <.L6>
   a:\tsext.w\ta0,a1
   e:\tret

0000000000000010 <.L6>:
  10:\tmv\ta1,a2
  12:\tsext.w\ta0,a1
  16:\tret

0000000000000018 <.L4>:
  18:\tmv\ta0,a1
  1a:\tret
"""

AARCH64_DUMP = """
shapes-aarch64.o:     file format elf64-littleaarch64


Disassembly of section .text:

0000000000000000 <sysfs_clamp>:
   0:\tcmp\tw0, w1
   4:\tb.lt\t14 <sysfs_clamp+0x14>  // b.tstop
   8:\tcmp\tw0, w2
   c:\tcsel\tw0, w0, w2, le
  10:\tret
"""


# -- pulling a function out of a dump ------------------------------------------------------


def test_extract_keeps_the_whole_function_past_local_labels():
    """The regression. A scan for the next ``<name>:`` header stops at ``.L6`` and loses the rest."""
    text = extract(RISCV_DUMP, "sysfs_clamp")
    assert text.splitlines()[-1].endswith("ret")
    assert "<.L4>:" in text, "the listing was truncated at the first local label"
    assert text.count("ret") == 3, "a three-exit function came back with fewer exits"


def test_extract_drops_the_preamble():
    """The file-name line is a path, and a path differs between a laptop, CI and the board."""
    text = extract(RISCV_DUMP, "sysfs_clamp")
    assert "file format" not in text
    assert "Disassembly of section" not in text
    assert text.startswith("0000000000000000 <sysfs_clamp>:")


def test_extract_says_what_is_actually_there():
    with pytest.raises(SymbolNotFoundError) as raised:
        extract(RISCV_DUMP, "sysfs_clmap")
    assert "sysfs_clamp" in str(raised.value), "the message should name the symbols present"


def test_symbols_includes_the_local_labels():
    """Not a wart: it is how the error message can suggest the name you meant."""
    assert symbols(RISCV_DUMP) == ["sysfs_clamp", ".L6", ".L4"]


@pytest.mark.parametrize(("dump", "expected"), [(RISCV_DUMP, "riscv64"), (AARCH64_DUMP, "aarch64")])
def test_architecture_comes_from_the_object_file(dump: str, expected: str):
    """objdump read the ELF header. A target name is just a string somebody typed."""
    assert architecture(dump) == expected


def test_architecture_refuses_to_guess():
    with pytest.raises(ValueError, match="file format"):
        architecture("no header here")


# -- flags and tools -----------------------------------------------------------------------


def test_code_flags_drops_what_cannot_change_an_instruction():
    flags = code_flags(("-O2", "-g", "-Wall", "-march=rv64gc", "-static"))
    assert flags == ("-O2", "-Wall", "-march=rv64gc")


def test_code_flags_keeps_optimisation():
    """The one flag that must never be silently dropped: -O0 and -O2 are different experiments."""
    assert "-O2" in code_flags(flags_for("aarch64"))


def test_objdump_matches_a_cross_compiler():
    assert objdump_for("aarch64-linux-gnu-gcc").startswith("aarch64-linux-gnu-")


def test_instructions_counts_instructions_not_labels():
    listing = Listing(
        symbol="x", text=extract(RISCV_DUMP, "sysfs_clamp"), arch="riscv64", toolchain={}
    )
    # Ten instructions across three blocks, and the three block headers are not instructions.
    assert listing.instructions == 10


# -- the whole path, where a toolchain exists ----------------------------------------------


@pytest.mark.hostcode
@pytest.mark.parametrize("arch", sorted(WORLD))
def test_disassembles_both_architectures(arch: str, build_dir):
    """Each architecture's compiler produces a complete listing for each published symbol."""
    try:
        target = target_for(arch)
    except Exception as exc:  # noqa: BLE001 — a missing cross compiler is a skip, not a failure
        pytest.skip(f"no {arch} toolchain here: {exc}")

    for symbol in SHAPES_SYMBOLS:
        listing = disassemble([SHAPES_SOURCE], symbol, target, build_dir=build_dir)
        assert listing.arch == arch
        assert listing.text.startswith(f"{'0' * 16} <{symbol}>:") or f"<{symbol}>:" in listing.text
        assert listing.text.rstrip().endswith("ret"), (
            f"{arch} {symbol} does not end in a return — the listing is truncated"
        )
        assert listing.instructions >= 2
        assert "-g" not in listing.toolchain["flags"]


@pytest.mark.hostcode
def test_the_two_architectures_disagree_about_clamp():
    """The teaching claim in ch00, asserted rather than hoped for.

    If a future compiler starts emitting a conditional select on RISC-V, or stops emitting one on
    AArch64, the chapter's explanation is wrong and this is where that surfaces — before a reader
    reads a paragraph about an instruction that is no longer in the listing above it.
    """
    texts = {}
    for arch in WORLD:
        try:
            target = target_for(arch)
        except Exception:  # noqa: BLE001
            pytest.skip(f"needs both cross compilers; {arch} is missing")
        texts[arch] = disassemble([SHAPES_SOURCE], "sysfs_clamp", target).text

    assert "csel" in texts["aarch64"], "ch00 says AArch64 selects rather than branches"
    assert "csel" not in texts["riscv64"]
    assert texts["riscv64"].count("ret") > texts["aarch64"].count("ret"), (
        "ch00 says the RISC-V version needs more exits"
    )


@pytest.mark.hostcode
def test_the_two_assemblers_divide_the_work_differently():
    """ch00 tells the reader to run readelf and see this. It should be there when they do.

    RISC-V leaves every intra-function branch as a relocation against a local label, because the
    linker may still relax the code and change the distances; AArch64's assembler settles them and
    the labels go. It is also the reason a listing cannot be cut at the next symbol header — see
    the module docstring — so this pins the behaviour that made that bug possible.
    """
    import subprocess  # noqa: PLC0415

    text_relocations = {}
    for arch in WORLD:
        try:
            target = target_for(arch)
        except Exception:  # noqa: BLE001
            pytest.skip(f"needs both cross compilers; {arch} is missing")
        disassemble([SHAPES_SOURCE], "sysfs_clamp", target)  # for its side effect: the object file
        readelf = target.cc.replace("gcc", "readelf")
        objects = list((ROOT / "sysfs" / "build").glob(f"shapes-{arch}.o"))
        assert objects, f"no {arch} object file to inspect"
        out = subprocess.run(
            [readelf, "-rW", str(objects[0])], capture_output=True, text=True, check=True
        ).stdout
        text_relocations[arch] = [
            line for line in out.splitlines() if "R_" in line and ".L" in line
        ]

    assert text_relocations["riscv64"], "RISC-V should relocate its own branches"
    assert not text_relocations["aarch64"], "AArch64's assembler should have settled them"


@pytest.mark.hostcode
def test_capture_is_a_listing_not_a_measurement():
    try:
        payload = capture("aarch64")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"no aarch64 toolchain here: {exc}")

    assert payload["kind"] == "listing"
    assert payload["machine"]["measured_under"] == "compilation"
    assert set(payload["summary"]["listings"]) == set(SHAPES_SYMBOLS)
