"""The reader's sharing model, built once for the real-hardware ordering chapter's three problems."""

from __future__ import annotations

import pytest

from tests.memory_ordering_on_real_hardware.harness import build


@pytest.fixture(scope="session")
def sharing(build_dir):
    return build(build_dir)
