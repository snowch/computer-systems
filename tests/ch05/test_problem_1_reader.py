"""Checks Problem 5.1 against the book's own reader, on a real xv6 binary.

The expected answers are not stored. They are computed by `sysfs/tools/elfdump.c` — which does not
contain either of the functions the reader is writing — so the target moves with the binary rather
than being a constant that goes stale the next time xv6 is rebuilt.
"""

from __future__ import annotations

import subprocess

import pytest

from bench import xv6
from bench.measure import PORTABLE_FLAGS, HostTarget, compile_program
from bench.run_elf import READER, parse
from bench.stamp import ROOT

SUBJECT = "_sameanswer"
NATIVE = HostTarget(name="native-other", cc="cc", flags=PORTABLE_FLAGS)


@pytest.fixture(scope="module")
def binary():
    if xv6.missing_requirements():
        pytest.skip(f"xv6 target: {'; '.join(xv6.missing_requirements())}")
    xv6.build()
    path = xv6.STAGE / "user" / SUBJECT
    assert path.exists(), path
    return path


@pytest.fixture(scope="module")
def truth(binary, build_dir):
    """What the book's finished reader says about the same file."""
    built = compile_program([READER], build_dir / "elfdump_truth", NATIVE)
    printed = subprocess.run(
        [str(built.path), str(binary)], capture_output=True, text=True, check=True
    ).stdout
    return parse(printed)


@pytest.fixture(scope="module")
def answered(binary, truth, build_dir):
    """What the reader's version says, asked about the same addresses."""
    built = compile_program(
        [ROOT / "tests" / "ch05" / "reader.c"], build_dir / "ch05reader", NATIVE
    )
    probes = [str(section["addr"]) for section in truth["sections"] if section["addr"]]
    printed = subprocess.run(
        [str(built.path), str(binary), *probes], capture_output=True, text=True, check=True
    ).stdout
    out = {"footprint": 0, "covering": {}}
    for line in printed.splitlines():
        parts = line.split()
        if parts[:1] == ["footprint"]:
            out["footprint"] = int(parts[1])
        elif parts[:1] == ["covering"]:
            out["covering"][int(parts[1])] = parts[2]
    return out


@pytest.mark.problem
def test_the_memory_footprint_matches(answered, truth):
    expected = sum(segment["memory_bytes"] for segment in truth["segments"])
    assert answered["footprint"] == expected, (
        "count what the loader has to provide, which is not the same as the size of the file"
    )


@pytest.mark.problem
def test_each_section_start_is_attributed_to_its_own_section(answered, truth):
    for section in truth["sections"]:
        if not section["addr"] or not section["size"]:
            continue
        named = answered["covering"].get(section["addr"])
        assert named == section["name"], (
            f"address {section['addr']} is the start of {section['name']!r}; "
            f"your reader said {named!r}"
        )


def test_the_book_reader_does_not_contain_the_answer():
    """Scaffolding: the problem is only a problem while elfdump lacks these two functions."""
    source = (ROOT / READER).read_text()
    assert "reader_memory_footprint" not in source
    assert "reader_section_covering" not in source
