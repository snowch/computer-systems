"""The machine-code chapter's stack walker finds the frames the source says are there.

The walk is the chapter's claim that a backtrace is a loop over a linked list. If the chain ever
comes back shorter than the call depth, either the walker is wrong or the compiler inlined
something it was asked not to — and both are worth failing over, because the chapter tells the
reader to expect one frame per call.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

import pytest

from bench.measure import ToolchainMissingError
from bench.run_disasm import target_for
from bench.stamp import ROOT

#: main → outer → middle → inner → walk. The walk starts inside `walk` itself, so it can climb
#: four frames before reaching main's caller.
EXPECTED_FRAMES = 3


@pytest.fixture(scope="module")
def walked() -> list[str]:
    runner = shutil.which("qemu-riscv64-static") or shutil.which("qemu-riscv64")
    if not runner:
        pytest.skip("no user-mode QEMU to run RV64 with (see the setup chapter)")
    try:
        target_for("riscv64")
    except ToolchainMissingError as error:
        pytest.skip(str(error))
    run = subprocess.run(
        [sys.executable, "./run", "framewalk"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return run.stdout.strip().splitlines()


@pytest.mark.hostcode
def test_the_walk_climbs_every_frame(walked):
    frames = [line for line in walked if line.startswith("frame ") and "bytes" in line]
    assert len(frames) >= EXPECTED_FRAMES, (
        "the walker found fewer frames than there are calls:\n" + "\n".join(walked)
    )


@pytest.mark.hostcode
def test_the_walk_stops_rather_than_wandering(walked):
    """The check the chapter draws attention to: it must refuse the outermost saved pointer."""
    assert any(line.endswith(" end") for line in walked), "\n".join(walked)
    assert walked[-1] == "end walk", "\n".join(walked)
