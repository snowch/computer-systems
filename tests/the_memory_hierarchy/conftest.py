"""The reader's hierarchy analysis, built once for the memory-hierarchy chapter's three problems."""

from __future__ import annotations

import pytest

from tests.the_memory_hierarchy.harness import build


@pytest.fixture(scope="session")
def hierarchy(build_dir):
    return build(build_dir)
