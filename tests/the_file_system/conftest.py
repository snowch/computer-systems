"""The reader's file-system model, built once for chapter 12's three problems."""

from __future__ import annotations

import pytest

from tests.the_file_system.harness import build


@pytest.fixture(scope="session")
def filesystem(build_dir):
    return build(build_dir)
