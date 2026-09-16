"""The reader's scheduling code, built once for the scheduling chapter's three problems."""

from __future__ import annotations

import pytest

from tests.scheduling_and_context_switches.harness import build


@pytest.fixture(scope="session")
def scheduling(build_dir):
    return build(build_dir)
