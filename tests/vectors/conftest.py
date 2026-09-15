"""The reader's lane arithmetic, built once for chapter 21's three problems."""

from __future__ import annotations

import pytest

from tests.vectors.harness import build


@pytest.fixture(scope="session")
def lanes(build_dir):
    return build(build_dir)
