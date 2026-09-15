"""The reader's fault-policy code, built once for chapter 8's three problems."""

from __future__ import annotations

import pytest

from tests.ch15.harness import build


@pytest.fixture(scope="session")
def policy(build_dir):
    return build(build_dir)
