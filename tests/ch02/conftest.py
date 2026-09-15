"""The reader's kernel-C exercises, built once for chapter 2's three problems."""

from __future__ import annotations

import pytest

from tests.ch02.harness import build


@pytest.fixture(scope="session")
def runtime(build_dir):
    return build(build_dir)
