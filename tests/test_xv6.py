"""The xv6 target: it builds, it boots, it answers, and it stays out of the submodule."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from bench import xv6
from bench.measure import compile_program
from bench.run_setup import HOST_PROBE, parse_probe
from bench.stamp import ROOT

pytestmark = pytest.mark.xv6


@pytest.fixture(scope="module")
def booted():
    return xv6.boot(["sysprobe", "ls"], timeout=180)


def test_it_reaches_a_shell(booted):
    assert not booted.timed_out, booted.transcript[-2000:]
    assert "init: starting sh" in booted.transcript


def test_every_hart_starts(booted):
    """A kernel that boots on one hart and hangs the rest still prints a prompt."""
    started = booted.transcript.count(" starting")
    assert started >= booted.cpus - 1, f"only {started} secondary harts announced themselves"


def test_the_book_s_program_is_in_the_image(booted):
    assert "sysprobe" in booted.output_of("ls")


def test_staging_leaves_the_submodule_clean():
    """Never a modified copy. The submodule is upstream and must stay byte-identical to it."""
    xv6.prepare()
    status = subprocess.run(
        ["git", "-C", str(xv6.XV6_SUBMODULE), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert status == "", f"the xv6 submodule has been modified:\n{status}"


def test_shared_headers_reach_the_staging_tree():
    stage = xv6.prepare()
    assert (stage / "sysfs" / "probe.h").exists(), (
        "sysfs/include/sysfs/*.h must be staged so xv6 programs can include them"
    )


def test_patches_apply_or_say_why():
    """Every patch in xv6/patches applies to the pinned commit. A stale one fails loudly."""
    for patch in sorted(xv6.PATCHES_DIR.glob("*.patch")):
        assert patch.stat().st_size > 0, f"{patch.name} is empty"
    xv6.prepare(force=True)  # raises with the patch name and git's message if one does not apply


@pytest.mark.hostcode
def test_both_targets_give_the_same_answers(booted, host_target, build_dir: Path):
    """The whole of the setup chapter's claim, in one assertion.

    The same header, compiled by two toolchains against two libraries for two different systems,
    reports identical sizes, identical layouts and identical byte order. Everything the book says
    about *what a program does* transfers between the targets. Everything it says about what a
    program *costs* does not, and no test can tell you that — only the board can.
    """
    built = compile_program(
        [HOST_PROBE], build_dir / "sysprobe-host", host_target, includes=["sysfs/include"]
    )
    on_host = parse_probe(built.run().stdout)
    on_xv6 = parse_probe(booted.output_of("sysprobe"))

    assert on_host["world"] == "host"
    assert on_xv6["world"] == "xv6"
    for field in ("types", "layouts", "offsets", "endian"):
        assert on_host[field] == on_xv6[field], f"the two targets disagree about {field}"


def test_a_missing_toolchain_is_reported_in_words(monkeypatch):
    """The error a reader gets when nothing is installed has to name what to install."""
    monkeypatch.setattr("bench.xv6.shutil.which", lambda _: None)
    monkeypatch.setattr("bench.xv6.XV6_SUBMODULE", Path(ROOT) / "does-not-exist")
    problems = xv6.missing_requirements()
    assert len(problems) == 3
    assert any("qemu-system-riscv64" in problem for problem in problems)
    assert any("submodule" in problem for problem in problems)
