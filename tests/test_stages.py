"""Claims Part I makes about emitted code, asserted so a compiler changing its mind fails CI.

ch01's program says the same thing on both targets and the compiler folds one route away; ch03's
array parameter is a pointer parameter, and its volatile reads all survive.

Two claims the chapter makes, checked rather than asserted. The first is the point of having two
targets at all: identical source, identical output, two machines that agree about what a program
computes and will disagree about everything else.
"""

from __future__ import annotations

import pytest

from bench import xv6
from bench.disasm import disassemble
from bench.measure import compile_program
from bench.run_disasm import target_for
from bench.stamp import ROOT

HOST_PROGRAM = "sysfs/tools/sameanswer.c"
EXPECTED = ["span 64", "folded 2016", "counted 2016", "agree yes", "end sameanswer"]


def _facts(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][1:]


@pytest.mark.hostcode
def test_the_host_build_agrees_with_itself(host_target, build_dir):
    """Both routes to the sum return the same number, which is the program's whole assertion."""
    built = compile_program(
        [HOST_PROGRAM], build_dir / "sameanswer", host_target, includes=["sysfs/include"]
    )
    assert _facts(built.run().stdout) == EXPECTED


@pytest.mark.xv6
def test_both_targets_print_the_same_facts():
    """The claim ch01 closes on. Only the first line, naming the world, may differ."""
    result = xv6.boot(["sameanswer"])
    assert not result.timed_out, result.transcript[-1500:]
    assert _facts(result.output_of("sameanswer")) == EXPECTED


@pytest.mark.hostcode
def test_only_one_of_the_two_routes_survives_to_run_time():
    """ch01's central contrast, asserted so that a compiler changing its mind fails the build.

    The chapter prints both listings and spends a section on why they differ. If a future compiler
    folds the counted loop too — or stops folding the other — the prose around those listings is
    wrong, and this is where that surfaces.
    """
    target = target_for("riscv64")
    folded = disassemble(
        ["sysfs/lib/stages.c"], "sysfs_sum_folded", target, includes=["sysfs/include"]
    )
    counted = disassemble(
        ["sysfs/lib/stages.c"], "sysfs_sum_counted", target, includes=["sysfs/include"]
    )
    assert folded.instructions < counted.instructions, (
        "ch01 says the folded route is the shorter one:\n" + folded.text
    )
    assert "2016" in folded.text or "0x7e0" in folded.text, (
        "ch01 says the compiler wrote the answer into the instruction stream:\n" + folded.text
    )


def test_the_walk_script_is_the_one_the_chapter_quotes():
    """Scaffolding: the four stages exist in the script, in the order the figure draws them."""
    script = (ROOT / "sysfs" / "tools" / "stages.sh").read_text()
    order = [script.index(f"# {n}. ") for n in (1, 2, 3, 4)]
    assert order == sorted(order), "stages.sh no longer walks the stages in order"


@pytest.mark.hostcode
def test_an_array_parameter_compiles_to_a_pointer_parameter():
    """ch03 claims these are identical instruction for instruction. Claims get checked.

    The chapter prints one of the two listings and says the other is the same, which saves the
    reader a page of duplicate output and costs the book nothing — provided something asserts it.
    """
    target = target_for("riscv64")
    array = disassemble(
        ["sysfs/lib/addresses.c"], "sysfs_sum_array", target, includes=["sysfs/include"]
    )
    pointer = disassemble(
        ["sysfs/lib/addresses.c"], "sysfs_sum_pointer", target, includes=["sysfs/include"]
    )

    def body(text: str) -> list[str]:
        # Everything after the symbol header, with the offsets stripped: two functions at
        # different addresses in the same object file are not expected to share those.
        return [line.split(":\t", 1)[1] for line in text.splitlines() if ":\t" in line]

    assert body(array.text) == body(pointer.text), (
        "ch03 says an array parameter and a pointer parameter produce the same code:\n"
        f"{array.text}\n\n{pointer.text}"
    )


@pytest.mark.hostcode
def test_volatile_keeps_every_read():
    """The other claim ch03 rests on: a plain read may be elided and a volatile one may not."""
    target = target_for("riscv64")
    plain = disassemble(
        ["sysfs/lib/addresses.c"], "sysfs_read_four", target, includes=["sysfs/include"]
    )
    marked = disassemble(
        ["sysfs/lib/addresses.c"], "sysfs_read_four_volatile", target, includes=["sysfs/include"]
    )
    assert plain.text.count("lw") == 1, "ch03 says the plain version reads once:\n" + plain.text
    assert marked.text.count("lw") == 4, "ch03 says volatile keeps all four reads:\n" + marked.text


def test_the_trap_probe_matches_the_program_it_counts():
    """ch06's census is only reproducible while the runner and the workload agree.

    `trapload.c` decides how many times it calls `getpid` and `bench/run_traps.py` asserts that
    the kernel counted exactly that many. Two constants in two languages, and nothing but this
    keeps them in step.
    """
    from bench.run_traps import PROBE_CALLS  # noqa: PLC0415

    source = (ROOT / "xv6" / "apps" / "trapload.c").read_text()
    assert f"#define SYSFS_TRAPLOAD_CALLS {PROBE_CALLS}" in source, (
        f"bench/run_traps.py expects {PROBE_CALLS} calls; trapload.c disagrees"
    )
