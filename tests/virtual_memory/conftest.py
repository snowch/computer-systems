"""The reader's page-table program, built once for the virtual-memory chapter's three problems."""

from __future__ import annotations

import pytest

from tests.virtual_memory.harness import build


@pytest.fixture(scope="session")
def walk(build_dir):
    """The reader's walk.c, compiled. All three problems live in it."""
    return build(build_dir)
