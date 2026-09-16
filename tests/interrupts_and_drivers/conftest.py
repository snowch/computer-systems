"""The reader's console model, built once for the drivers chapter's problems."""

from __future__ import annotations

import pytest

from tests.interrupts_and_drivers.harness import build


@pytest.fixture(scope="session")
def console(build_dir):
    return build(build_dir)
