"""The reader's profile reader, built once for chapter 20's three problems."""

from __future__ import annotations

import pytest

from tests.ch22.harness import build


@pytest.fixture(scope="session")
def profiler(build_dir):
    return build(build_dir)
