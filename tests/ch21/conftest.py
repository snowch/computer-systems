"""The reader's cost model, built once for chapter 19's three problems."""

from __future__ import annotations

import pytest

from tests.ch21.harness import build


@pytest.fixture(scope="session")
def oscost(build_dir):
    return build(build_dir)
