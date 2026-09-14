"""Which tests can run here, and why the rest are skipped.

Three markers, one per capability. A test that needs something this machine does not have skips
itself with a message that names what is missing, rather than failing and teaching everyone to
ignore a red suite.

    board     the machine being measured. Timing only, and never satisfied by an emulator.
    xv6       qemu-system-riscv64 plus the submodule.
    hostcode  any way to build and run host-target code for a board architecture — the machine
              itself, or a cross compiler plus user-mode QEMU in CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench import xv6  # noqa: E402
from bench.measure import resolve_host_target  # noqa: E402
from bench.stamp import classify_machine  # noqa: E402


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    xv6_problems = xv6.missing_requirements()
    on_board = classify_machine() == "board"
    try:
        host_target = resolve_host_target()
        # Anything but the fallback: a native board build or a cross build for one.
        host_path = host_target.name != "native-other"
        host_why = host_target.why
    except Exception as exc:  # noqa: BLE001 — reported, not raised, so the suite still runs
        host_path, host_why = False, str(exc)

    for item in items:
        if "xv6" in item.keywords and xv6_problems:
            item.add_marker(pytest.mark.skip(reason=f"xv6 target: {'; '.join(xv6_problems)}"))
        if "board" in item.keywords and not on_board:
            item.add_marker(
                pytest.mark.skip(
                    reason="needs the machine being measured; timings are never taken elsewhere"
                )
            )
        if "hostcode" in item.keywords and not host_path:
            item.add_marker(
                pytest.mark.skip(reason=f"no host-target execution path here ({host_why})")
            )


@pytest.fixture(scope="session")
def host_target():
    """How host-target C can be built and run here."""
    return resolve_host_target()


@pytest.fixture(scope="session")
def build_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("sysfs-build")
