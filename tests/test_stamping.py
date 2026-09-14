"""The guards that stop a number the book cannot defend from reaching a reader.

Every test here is a failure mode that has to stay impossible. The most important of them is
:func:`test_host_result_from_an_emulator_is_rejected`: an emulated timing looks exactly like a
measured one, so nothing but a check like this can tell them apart.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from bench.figures import FIGURES, KINDS, Table, cited_results, pending_results
from bench.stamp import (
    REQUIRED_STAMPS,
    RESULTS_DIR,
    ROOT,
    build_result,
    code_fingerprint,
    describe_toolchain,
    measurement_differences,
    normalise_isa,
    provenance_problems,
    write_result,
)

VERIFY = ROOT / "scripts" / "verify-numbers.py"


def test_the_verifier_itself_passes_on_this_repository():
    """Run the script CI runs, not just the functions it calls.

    A test that exercised only the helpers would keep passing while the entry point was broken,
    which has happened often enough elsewhere to be worth one subprocess.
    """
    result = subprocess.run(
        [sys.executable, str(VERIFY)], capture_output=True, text=True, cwd=ROOT, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def sample(**overrides) -> dict:
    payload = build_result(
        name="sample",
        target="xv6",
        summary={"kernel_bytes": 1024},
        code_sources=["bench/run_setup.py"],
        toolchain={"cc": "gcc (test)", "flags": "-O2"},
        machine={"kind": "qemu", "arch": "riscv64", "kernel": "xv6 @ test", "model": "qemu virt"},
    )
    payload.update(overrides)
    return payload


def test_every_committed_result_carries_every_stamp():
    for path in sorted(RESULTS_DIR.glob("*.json")):
        payload = json.loads(path.read_text())
        missing = [stamp for stamp in REQUIRED_STAMPS if stamp not in payload]
        assert not missing, f"{path.name} is missing {missing}"


def test_every_committed_result_matches_the_code_it_names():
    for path in sorted(RESULTS_DIR.glob("*.json")):
        payload = json.loads(path.read_text())
        expected = code_fingerprint(payload["code_sources"], payload["target"])
        assert payload["code_fingerprint"] == expected, (
            f"{path.name} was produced by code that has since changed — re-run its runner"
        )


def test_fingerprint_changes_when_a_source_changes(tmp_path: Path, monkeypatch):
    """The whole mechanism rests on this: edit the code, invalidate the number."""
    before = code_fingerprint(["bench/run_setup.py"])
    scratch = tmp_path / "extra.py"
    scratch.write_text("# a source that did not exist before\n")
    monkeypatch.setattr("bench.stamp.ROOT", tmp_path)
    (tmp_path / "bench").mkdir()
    (tmp_path / "bench" / "measure.py").write_text("# different core\n")
    after = code_fingerprint(["extra.py"])
    assert before != after


def test_fingerprint_refuses_a_missing_source():
    with pytest.raises(FileNotFoundError):
        code_fingerprint(["sysfs/lib/does-not-exist.c"])


def listing_sample(**overrides) -> dict:
    payload = build_result(
        name="sample-listing",
        target="host",
        kind="listing",
        summary={
            "source": "sysfs/lib/shapes.c",
            "listings": {
                "f": {"symbol": "f", "text": "0 <f>:\n  0:\tret", "instructions": 1},
            },
        },
        code_sources=["bench/run_disasm.py"],
        toolchain={"cc": "gcc (test)", "flags": "-O2 -c"},
        machine=describe_toolchain("aarch64"),
    )
    payload.update(overrides)
    return payload


def test_a_listing_needs_no_board():
    """The exemption. Instructions do not depend on which computer ran the compiler, so a `host`
    listing produced on a CI runner is exactly as good as one produced on the board."""
    assert provenance_problems("fake", listing_sample()) == []


def test_a_timing_relabelled_as_a_listing_is_still_rejected():
    """The exemption's cost, and the reason listings have rules of their own.

    Without this, `kind: listing` would be a one-word way round the check the whole repository is
    built on: declare a laptop timing a listing and it would skip the board rule entirely.
    """
    payload = listing_sample()
    payload["summary"]["median_ns"] = 120
    problems = provenance_problems("fake", payload)
    assert problems and "timing" in " ".join(problems).lower()


def test_a_listing_that_claims_to_have_run_is_rejected():
    payload = listing_sample(machine={"kind": "board", "measured_under": "native"})
    problems = provenance_problems("fake", payload)
    assert problems and "compiled, not run" in " ".join(problems)


def test_an_empty_listing_is_rejected():
    """A chapter with a blank code block in it is worse than one with no code block."""
    payload = listing_sample()
    payload["summary"]["listings"]["f"]["text"] = "\n  \n"
    problems = provenance_problems("fake", payload)
    assert problems and "empty" in " ".join(problems)


def test_a_result_with_no_kind_is_judged_as_a_measurement():
    """Old results predate the field. Reading absence as 'measurement' holds them to the stricter
    rules; reading it as 'listing' would let them past both sets."""
    payload = sample(target="host", machine={"kind": "other", "measured_under": "native"})
    del payload["kind"]
    assert provenance_problems("fake", payload)


def test_unknown_kind_is_refused():
    with pytest.raises(ValueError, match="unknown kind"):
        build_result(
            name="x",
            target="xv6",
            kind="anecdote",
            summary={},
            code_sources=[],
            toolchain={},
            machine={},
        )


def test_unknown_target_is_refused():
    with pytest.raises(ValueError, match="unknown target"):
        build_result(
            name="x",
            target="laptop",
            summary={},
            code_sources=[],
            toolchain={},
            machine={},
        )


def test_a_result_round_trips(tmp_path: Path):
    payload = sample()
    path = write_result(payload, results_dir=tmp_path)
    assert json.loads(path.read_text()) == payload
    assert path.read_text().endswith("\n")


def test_host_result_from_an_emulator_is_rejected():
    """A `host` figure measured anywhere but the board is the failure this repository exists to
    prevent. QEMU will produce a plausible duration; it means nothing."""
    problems = provenance_problems(
        "fake", sample(target="host", machine={"kind": "qemu", "measured_under": "emulation"})
    )
    assert problems and "emulated" in " ".join(problems).lower()


def test_xv6_result_carrying_a_timing_is_rejected():
    problems = provenance_problems("fake", sample(summary={"loop_seconds": 0.5}))
    assert problems and "timing" in " ".join(problems).lower()


def test_board_result_passes_provenance():
    problems = provenance_problems(
        "fake",
        sample(
            target="host",
            machine={"kind": "board", "arch": "riscv64", "measured_under": "native"},
        ),
    )
    assert problems == []


def test_every_cited_result_exists():
    for name in sorted(cited_results()):
        assert (RESULTS_DIR / f"{name}.json").exists(), f"{name}.json is cited but missing"


def test_pending_figures_have_no_result_yet():
    """If the measurement has landed, the pending marker must come off in the same commit."""
    for name, reason in pending_results().items():
        assert not (RESULTS_DIR / f"{name}.json").exists(), (
            f"{name}.json exists but its figure still says {reason!r}"
        )


def test_pending_figures_name_the_command_that_fixes_them():
    for name, figure in FIGURES.items():
        if isinstance(figure, Table) and figure.pending:
            assert "make bench-board" in figure.pending, (
                f"{name}'s pending reason should tell the author what to run"
            )


def test_every_figure_is_a_kind_something_renders():
    for name, figure in FIGURES.items():
        assert isinstance(figure, KINDS), name


def test_isa_strings_normalise():
    assert normalise_isa("RV64IMAFDC ") == normalise_isa("rv64imafdc")


def test_environmental_stamps_do_not_count_as_a_changed_measurement():
    """The bug that made CI red on its first run.

    ``generated_at`` changes on every run and ``recorded_on`` describes the machine driving the
    tooling — a CI runner, not the system under study. A comparison that counted either would
    report a difference every time, including on the same machine a second later.
    """
    committed = sample()
    fresh = sample(
        generated_at="2030-01-01T00:00:00+00:00",
        recorded_on={"kind": "other", "arch": "x86_64", "kernel": "Linux 6.17.0-azure"},
    )
    assert measurement_differences(committed, fresh) == []


def test_a_moved_measurement_is_reported_with_its_path():
    committed = sample(summary={"kernel_bytes": 276112, "types": [{"name": "int", "size": 4}]})
    fresh = sample(summary={"kernel_bytes": 280000, "types": [{"name": "int", "size": 8}]})
    differences = measurement_differences(committed, fresh)
    assert "summary.kernel_bytes: 276112, now 280000" in differences
    assert "summary.types[0].size: 4, now 8" in differences


def test_added_and_removed_summary_keys_are_reported():
    differences = measurement_differences(sample(summary={"a": 1}), sample(summary={"b": 2}))
    assert any("gone" in difference for difference in differences)
    assert any("added" in difference for difference in differences)


def test_a_longer_list_is_reported_rather_than_zipped_silently():
    """zip() would drop the extra entry and call the measurement unchanged."""
    committed = sample(summary={"types": [{"size": 4}]})
    fresh = sample(summary={"types": [{"size": 4}, {"size": 8}]})
    assert measurement_differences(committed, fresh) == ["summary.types: 1 entries, now 2"]


def test_context_blocks_are_not_part_of_the_measurement():
    """A runner whose QEMU or compiler is a version ahead still agrees about the answers.

    Those blocks are provenance, and provenance is verify-numbers.py's job. Failing here on a
    QEMU minor version would make the check noise, and a noisy check gets ignored.
    """
    committed = sample()
    fresh = sample(
        machine={"kind": "qemu", "emulator": "QEMU emulator version 9.9.9", "kernel": "xv6 @ test"},
        toolchain={"cc": "riscv64-linux-gnu-gcc 14.0.0", "flags": "-O2"},
    )
    assert measurement_differences(committed, fresh) == []
