"""The reader's sharing model, built once for chapter 18's three problems."""

from __future__ import annotations

import pytest

from tests.ch20.harness import build


@pytest.fixture(scope="session")
def sharing(build_dir):
    return build(build_dir)
