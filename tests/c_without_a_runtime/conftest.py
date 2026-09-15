"""The reader's kernel-C exercises, built once for chapter 2's three problems."""

from __future__ import annotations

import pytest

from tests.c_without_a_runtime.harness import build


@pytest.fixture(scope="session")
def runtime(build_dir):
    return build(build_dir)
