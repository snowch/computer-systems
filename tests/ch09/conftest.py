"""The reader's page-table program, built once for chapter 7's three problems."""

from __future__ import annotations

import pytest

from tests.ch09.harness import build


@pytest.fixture(scope="session")
def walk(build_dir):
    """The reader's walk.c, compiled. All three problems live in it."""
    return build(build_dir)
