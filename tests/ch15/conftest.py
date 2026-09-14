"""The reader's hierarchy analysis, built once for chapter 15's three problems."""

from __future__ import annotations

import pytest

from tests.ch15.harness import build


@pytest.fixture(scope="session")
def hierarchy(build_dir):
    return build(build_dir)
