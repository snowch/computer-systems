"""Checks Problem 5.3 against messages produced by a real linker in this test run.

The messages are generated rather than quoted, so they are the ones the reader's own toolchain
produces. What the reader supplies is the cause; the test knows it because it constructed the
failure deliberately.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from tests.ch07.problem_3_diagnose import CAUSES, DIAGNOSES

CC = "riscv64-linux-gnu-gcc"
FLAGS = ["-O2", "-march=rv64gc", "-mabi=lp64d", "-static"]

#: Each broken build, and the cause it was built to have. The reader sees the message and the
#: key; they do not see this mapping.
_FAULTS = {
    "missing": (
        ["int absent(int);\nint main(void){ return absent(1); }"],
        "nothing defines it",
    ),
    "duplicate": (
        [
            "int shared(int x){ return x; }\nint main(void){ return shared(1); }",
            "int shared(int x){ return x + 1; }",
        ],
        "two things define it",
    ),
    "hidden_by_static": (
        [
            "int helper(int);\nint main(void){ return helper(1); }",
            "static int helper(int x){ return x; }\nint keep_it_used(void){ return helper(0); }",
        ],
        "defined, but private to its own file",
    ),
    "archive_first": (
        ["int packaged(int);\nint main(void){ return packaged(1); }"],
        "defined, but the linker had already passed it",
    ),
}

#: The one failure that cannot be built from two source files: an archive listed on the command
#: line *before* the object that needs it. A linker walks the line once, takes from an archive only
#: what is wanted at the moment it reaches it, and does not go back — which is why this fails while
#: the same two files in the other order do not.
_ARCHIVE_SOURCE = "int packaged(int x){ return x + 1; }"


@pytest.fixture(scope="module")
def messages(tmp_path_factory) -> dict[str, str]:
    if not shutil.which(CC):
        pytest.skip(f"{CC} is not installed (see ch00)")
    directory = tmp_path_factory.mktemp("diagnose")
    out: dict[str, str] = {}
    # The archive case needs one built first, and it is the reason this problem exists.
    member = directory / "packaged.c"
    member.write_text(_ARCHIVE_SOURCE + "\n")
    subprocess.run(
        [
            CC,
            *[f for f in FLAGS if f != "-static"],
            "-c",
            str(member),
            "-o",
            str(directory / "packaged.o"),
        ],
        check=True,
        capture_output=True,
    )
    archive = directory / "libpackaged.a"
    subprocess.run(
        [f"{CC[: -len('gcc')]}ar", "rcs", str(archive), str(directory / "packaged.o")],
        check=True,
        capture_output=True,
    )

    for key, (sources, _) in _FAULTS.items():
        paths = []
        for index, source in enumerate(sources):
            path = directory / f"{key}_{index}.c"
            path.write_text(source + "\n")
            paths.append(str(path))
        # The archive goes *before* the object that needs it, which is the whole fault.
        line = [str(archive), *paths] if key == "archive_first" else paths
        done = subprocess.run(
            [CC, *FLAGS, *line, "-o", str(directory / key)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode != 0, f"{key} was supposed to fail to link and did not"
        out[key] = (done.stderr + done.stdout).strip()
    return out


@pytest.mark.problem
@pytest.mark.parametrize("key", sorted(_FAULTS))
def test_the_reader_diagnosed_it(key: str, messages):
    assert DIAGNOSES, "Problem 5.3: DIAGNOSES is still empty"
    assert DIAGNOSES.get(key) in CAUSES, f"{key}: choose one of {CAUSES}"
    assert DIAGNOSES[key] == _FAULTS[key][1], (
        f"{key}: you said {DIAGNOSES[key]!r}. The linker said:\n{messages[key]}"
    )


def test_every_failure_really_fails(messages):
    """Scaffolding: a diagnosis exercise needs four failures, not four successes."""
    assert len(messages) == len(_FAULTS)
    assert all(text for text in messages.values()), "a linker failed silently"
