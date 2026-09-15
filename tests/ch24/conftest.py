"""The reader's predictor model, built once for chapter 17's problems."""

from __future__ import annotations

import pytest

from tests.ch24.harness import build


@pytest.fixture(scope="session")
def predictor(build_dir):
    return build(build_dir)
