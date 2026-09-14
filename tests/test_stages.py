"""Claims Part I makes about emitted code, asserted so a compiler changing its mind fails CI.

ch01's program says the same thing on both targets and the compiler folds one route away; ch03's
array parameter is a pointer parameter, and its volatile reads all survive.

Two claims the chapter makes, checked rather than asserted. The first is the point of having two
targets at all: identical source, identical output, two machines that agree about what a program
computes and will disagree about everything else.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from bench import xv6
from bench.disasm import disassemble
from bench.measure import compile_program
from bench.run_disasm import target_for
from bench.run_stages import CC, WalkError, parse_walk, refuse_a_size_that_describes_this_checkout
from bench.stamp import ROOT

HOST_PROGRAM = "sysfs/tools/sameanswer.c"
WALK_SCRIPT = "sysfs/tools/stages.sh"
WALK_HEADER = "sysfs/include/sysfs/stages.h"
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


def test_the_walk_refuses_a_file_that_names_this_checkout():
    """The guard itself, checked — a guard nobody has ever seen fire is a comment.

    It reads every file the walk produced rather than only the preprocessed one, because an
    object file or a binary that began embedding its build directory would move a recorded size
    the same way and would be much harder to attribute.
    """
    scratch = ROOT / "sysfs" / "build"
    scratch.mkdir(parents=True, exist_ok=True)
    planted = scratch / "walk-guard-probe.i"
    planted.write_text(f'# 1 "{ROOT}/sysfs/include/sysfs/stages.h" 1\n')
    try:
        with pytest.raises(WalkError, match="path of this checkout"):
            refuse_a_size_that_describes_this_checkout(scratch)
    finally:
        planted.unlink()


@pytest.mark.skipif(shutil.which(CC) is None, reason=f"needs {CC}")
def test_the_walk_measures_the_toolchain_and_not_the_checkout(tmp_path):
    """ch01's stage sizes must be the same in two clones of the same commit. They were not.

    An absolute `-I` put this checkout's path into the preprocessor's line markers and therefore
    into stage 1's byte count, so the same tree measured 38273 bytes on a laptop and 38345 on a CI
    runner — three line markers, twenty-four characters apart. No amount of reading the number
    would have found that. Measuring it twice from different depths finds it immediately, which is
    the only reason this test exists in the form it does.
    """
    walks = []
    roots = ("b", "a-deliberately-long-directory-name/" * 3 + "checkout")
    for name in roots:
        checkout = tmp_path / name
        for relative in (WALK_SCRIPT, HOST_PROGRAM, WALK_HEADER):
            copied = checkout / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            copied.write_bytes((ROOT / relative).read_bytes())
        printed = subprocess.run(
            ["sh", str(checkout / WALK_SCRIPT), HOST_PROGRAM, str(checkout / "build"), CC],
            cwd=checkout,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        walks.append(parse_walk(printed))

    shorter, longer = (len(str(tmp_path / name)) for name in roots)
    assert longer - shorter > 100, "the two checkouts must differ enough for a path to show up"
    assert walks[0] == walks[1], (
        "the same commit measured differently from two directories, so ch01's stage sizes are "
        f"partly a statement about where the tree lives:\n{walks[0]}\n{walks[1]}"
    )


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
