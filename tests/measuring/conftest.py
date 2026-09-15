"""The reader's measurement code, built once for chapter 14's three problems."""

from __future__ import annotations

import pytest

from tests.measuring.harness import build


@pytest.fixture(scope="session")
def measuring(build_dir):
    return build(build_dir)
