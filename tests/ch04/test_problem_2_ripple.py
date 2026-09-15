"""Checks Problem 1.2 by doing the experiment.

No expected answers are stored here, deliberately. The test copies the program, makes the change,
runs the toolchain, and compares the bytes each stage produced. Whatever the compiler does is the
right answer, including on a compiler that behaves differently from the author's — which is also
why the chapter does not tell you what happens.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from bench.stamp import ROOT
from tests.ch04.problem_2_ripple import CHANGES, STAGES, stages_disturbed_by

CC = "riscv64-linux-gnu-gcc"
FLAGS = ["-O2", "-Wall", "-march=rv64gc", "-mabi=lp64d", f"-I{ROOT / 'sysfs' / 'include'}"]

#: The program under the knife, and the header it takes its span from.
PROGRAM = ROOT / "sysfs" / "tools" / "sameanswer.c"
HEADER = ROOT / "sysfs" / "include" / "sysfs" / "stages.h"


def _edit(source: str, header: str, change: str) -> tuple[str, str]:
    """Apply one named change, exactly as the problem describes it."""
    if change == "add_a_comment":
        return source.replace(
            "int main(void) {", "/* one line of nothing */\nint main(void) {"
        ), header
    if change == "rename_a_local":
        # Only inside the two summing functions. The reporting macro below them contains "\n" in
        # a format string, and a word-boundary rename would happily rewrite that too.
        head, marker, tail = header.partition("#define SYSFS_STAGES_REPORT")
        return source, re.sub(r"\bn\b", "index", head) + marker + tail
    if change == "change_the_span":
        return source, header.replace(
            "#define SYSFS_STAGES_SPAN 64", "#define SYSFS_STAGES_SPAN 65"
        )
    if change == "add_an_uncalled_static":
        return (
            source.replace(
                "int main(void) {",
                "static int nobody_calls_this(void) { return 7; }\n\nint main(void) {",
            ),
            header,
        )
    raise AssertionError(f"unknown change {change!r}")


def _walk(directory: Path, source: str, header: str) -> dict[str, bytes]:
    """Run the four stages in one directory and return what each produced.

    Same directory and same filenames every time: the preprocessor writes the path it was given
    into its own output, so building two variants in two temporary directories would report a
    difference that is entirely about where the test happened to run.
    """
    (directory / "sysfs").mkdir(exist_ok=True)
    (directory / "sysfs" / "stages.h").write_text(header)
    program = directory / "sameanswer.c"
    program.write_text(source)

    flags = ["-O2", "-Wall", "-march=rv64gc", "-mabi=lp64d", f"-I{directory}"]
    steps = [
        (["-E", str(program), "-o", "p.i"], "preprocess", "p.i"),
        (["-S", "p.i", "-o", "p.s"], "compile", "p.s"),
        (["-c", "p.s", "-o", "p.o"], "assemble", "p.o"),
        (["-static", "p.o", "-o", "p"], "link", "p"),
    ]
    produced: dict[str, bytes] = {}
    for argv, stage, output in steps:
        subprocess.run([CC, *flags, *argv], cwd=directory, check=True, capture_output=True)
        produced[stage] = (directory / output).read_bytes()
    return produced


@pytest.fixture(scope="module")
def observed(tmp_path_factory) -> dict[str, set[str]]:
    """For each change: the stages whose output actually differed."""
    if not shutil.which(CC):
        pytest.skip(f"{CC} is not installed (see ch00)")

    source, header = PROGRAM.read_text(), HEADER.read_text()
    workspace = tmp_path_factory.mktemp("ripple")
    baseline = _walk(workspace, source, header)

    results: dict[str, set[str]] = {}
    for change in CHANGES:
        changed_source, changed_header = _edit(source, header, change)
        assert (changed_source, changed_header) != (source, header), (
            f"the edit for {change!r} changed nothing — the test harness is broken, not your answer"
        )
        after = _walk(workspace, changed_source, changed_header)
        results[change] = {stage for stage in STAGES if after[stage] != baseline[stage]}
    return results


@pytest.mark.problem
@pytest.mark.parametrize("change", sorted(CHANGES), ids=sorted(CHANGES))
def test_the_reader_predicted_the_ripple(change: str, observed):
    predicted = stages_disturbed_by(change)
    assert predicted == observed[change], (
        f"{CHANGES[change]}: you said {sorted(predicted) or 'nothing'} would change; "
        f"the toolchain changed {sorted(observed[change]) or 'nothing'}"
    )


def test_the_experiment_can_tell_the_changes_apart(observed):
    """Scaffolding: a puzzle where every change disturbs the same stages teaches nothing."""
    assert len({frozenset(stages) for stages in observed.values()}) > 1, (
        "every change disturbed the same stages — this problem has no signal in it"
    )


def test_at_least_one_change_reaches_the_binary(observed):
    """Scaffolding: and one where nothing ever reaches the binary is not about a toolchain."""
    assert any("link" in stages for stages in observed.values())
