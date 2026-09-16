"""The reader's predictor model, built once for the CPU chapter's problems."""

from __future__ import annotations

import pytest

from tests.the_cpu.harness import build


@pytest.fixture(scope="session")
def predictor(build_dir):
    return build(build_dir)
