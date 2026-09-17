"""The host-target correctness path: the book's C compiles for the reference architecture and
answers correctly.

Marked ``hostcode`` rather than ``board``, because this needs a way to *execute* host-target code
and not the reference *hardware*. On the machine that is native; in CI it is a cross compiler
plus user-mode QEMU. Nothing here is timed, and nothing here could be: see :mod:`bench.measure`.

The assertions are ABI facts, and they hold on both architectures the book supports — AArch64 and
RV64 are both LP64 and little-endian, which is itself the point the setup chapter makes with the probe.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bench.measure import compile_program
from bench.run_setup import HOST_PROBE, parse_probe
from bench.stamp import ROOT

pytestmark = pytest.mark.hostcode


@pytest.fixture(scope="module")
def probe(host_target, build_dir: Path) -> dict:
    built = compile_program(
        [HOST_PROBE], build_dir / "sysprobe", host_target, includes=["sysfs/include"]
    )
    return parse_probe(built.run().stdout)


def test_the_probe_identifies_itself(probe: dict):
    assert probe["world"] == "host"


def test_the_data_model_is_lp64(probe: dict):
    """`long` and pointers are 64-bit and `int` is 32-bit. That is a choice the ABI made."""
    sizes = {fact["name"]: fact["size"] for fact in probe["types"]}
    assert sizes["int"] == 4
    assert sizes["long"] == 8
    assert sizes["pointer"] == 8


def test_alignment_equals_size_for_the_scalar_types(probe: dict):
    """True on this ABI, and worth asserting because the representation chapter relies on it."""
    for fact in probe["types"]:
        assert fact["align"] == fact["size"], fact


def test_declaration_order_costs_bytes(probe: dict):
    """Same members, different order, different size. The compiler is not reordering them."""
    layouts = {fact["name"]: fact for fact in probe["layouts"]}
    assert layouts["declaration_order"]["size"] > layouts["size_order"]["size"]
    assert layouts["declaration_order"]["padding"] > layouts["size_order"]["padding"]


def test_it_is_little_endian(probe: dict):
    assert probe["endian"] == "little"


def test_the_middle_member_is_where_alignment_puts_it(probe: dict):
    assert probe["offsets"]["declaration_order.middle"] == 4


def test_a_compile_failure_reports_the_compiler_message(host_target, build_dir: Path):
    """A build error has to arrive as the compiler's own words, or debugging it is guesswork."""
    broken = build_dir / "broken.c"
    broken.write_text("int main(void) { return undefined_symbol; }\n")
    with pytest.raises(RuntimeError, match="undefined_symbol"):
        compile_program([broken], build_dir / "broken", host_target)


def test_the_probe_header_is_shared_verbatim():
    """The two targets compile the same bytes. That is what makes their agreement meaningful."""
    host = (ROOT / HOST_PROBE).read_text()
    xv6_app = (ROOT / "xv6" / "apps" / "sysprobe.c").read_text()
    for source in (host, xv6_app):
        assert '#include "sysfs/probe.h"' in source
        assert "SYSFS_PROBE_ALL(printf," in source
