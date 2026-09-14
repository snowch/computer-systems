"""ch01's program says the same thing on both targets, and the compiler folds one route away.

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
