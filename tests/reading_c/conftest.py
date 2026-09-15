"""The reader's exercises, built once for chapter 1's three problems."""

from __future__ import annotations

import pytest

from tests.reading_c.harness import build


@pytest.fixture(scope="session")
def declarations(build_dir):
    return build(build_dir)
