"""The reader's locking code, built once for chapter 10's three problems."""

from __future__ import annotations

import pytest

from tests.locks_and_memory_ordering.harness import build


@pytest.fixture(scope="session")
def locking(build_dir):
    return build(build_dir)
