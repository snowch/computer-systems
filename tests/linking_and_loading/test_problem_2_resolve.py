"""Checks Problem 5.2 by asking a linker.

Nothing is stored. Each pair is compiled and linked, and whether the link succeeded is the answer.
The last case is the interesting one and the test does not say why — it records what happened, and
the reader is expected to notice that a successful link is not the same as a correct program.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from tests.linking_and_loading.problem_2_resolve import CASES, LINKS

CC = "riscv64-linux-gnu-gcc"
FLAGS = ["-O2", "-march=rv64gc", "-mabi=lp64d", "-static"]


@pytest.fixture(scope="module")
def observed(tmp_path_factory) -> dict[str, bool]:
    if not shutil.which(CC):
        pytest.skip(f"{CC} is not installed (see ch00)")
    directory = tmp_path_factory.mktemp("resolve")
    results: dict[str, bool] = {}
    for name, (first, second) in CASES.items():
        a, b = directory / f"{name}_a.c", directory / f"{name}_b.c"
        a.write_text(first + "\n")
        b.write_text(second + "\n")
        done = subprocess.run(
            [CC, *FLAGS, str(a), str(b), "-o", str(directory / name)],
            capture_output=True,
            text=True,
            check=False,
        )
        results[name] = done.returncode == 0
    return results


@pytest.mark.problem
@pytest.mark.parametrize("case", sorted(CASES))
def test_the_reader_predicted_the_link(case: str, observed):
    assert LINKS, "Problem 5.2: LINKS is still empty"
    assert case in LINKS, f"no answer for {case!r}"
    assert LINKS[case] == observed[case], (
        f"{case}: you said it would {'link' if LINKS[case] else 'fail'} and it "
        f"{'linked' if observed[case] else 'failed'}. The two files were:\n"
        f"--- a\n{CASES[case][0]}\n--- b\n{CASES[case][1]}"
    )


def test_some_link_and_some_do_not(observed):
    """Scaffolding: five cases with the same outcome would be a problem with no content."""
    assert len(set(observed.values())) == 2, observed
