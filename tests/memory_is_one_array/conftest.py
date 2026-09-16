"""The reader's exercises, built once for the three problems of *Memory Is One Array*."""

from __future__ import annotations

import pytest

from tests.memory_is_one_array.harness import build


@pytest.fixture(scope="session")
def declarations(build_dir):
    return build(build_dir)
