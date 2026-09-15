"""The reader's scheduling code, built once for chapter 11's three problems."""

from __future__ import annotations

import pytest

from tests.ch18.harness import build


@pytest.fixture(scope="session")
def scheduling(build_dir):
    return build(build_dir)
