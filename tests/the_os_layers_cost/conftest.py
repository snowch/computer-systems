"""The reader's cost model, built once for the OS-cost chapter's three problems."""

from __future__ import annotations

import pytest

from tests.the_os_layers_cost.harness import build


@pytest.fixture(scope="session")
def oscost(build_dir):
    return build(build_dir)
