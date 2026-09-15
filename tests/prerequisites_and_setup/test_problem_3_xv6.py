"""Checks Problem 0.3 by booting the kernel with your program in it."""

from __future__ import annotations

import pytest

from bench import xv6
from bench.stamp import ROOT

SOURCE = ROOT / "tests" / "prerequisites_and_setup" / "ch00ping.c"

pytestmark = pytest.mark.xv6


@pytest.fixture(scope="module")
def transcript():
    """Boot xv6 with this one extra user program staged in.

    Your answer lives under tests/ and not in xv6/apps/ on purpose: a program that does not
    compile should fail your test, not everybody's kernel build.
    """
    return xv6.boot(["ch00ping 41"], extra_apps=[SOURCE], timeout=180)


def test_the_kernel_boots_with_your_program_in_it(transcript):
    """Scaffolding: staging, cross-compiling, imaging and booting all worked.

    This is the half chapter 0 is responsible for. If it passes and the next test fails, the
    toolchain is fine and the C is yours to write.
    """
    assert not transcript.timed_out, "xv6 never reached a shell"
    assert "ch00ping" in transcript.transcript, "the program was never staged into the image"
    assert "exec ch00ping failed" not in transcript.transcript, (
        "the shell could not run it — did it compile into the file system image?"
    )


@pytest.mark.problem
def test_it_says_pong(transcript):
    output = transcript.output_of("ch00ping 41")
    assert output, (
        "ch00ping printed nothing. Open tests/prerequisites_and_setup/ch00ping.c — the TODO is still there."
    )
    assert "pong 42" in output, (
        f"expected a line reading `pong 42`, got:\n{output}\n"
        "argv[1] is a string; xv6's user library has atoi."
    )
