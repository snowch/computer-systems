"""The reader's crossing model, built once for chapter 13's three problems."""

from __future__ import annotations

import pytest

from tests.the_same_program_on_both_targets.harness import build


@pytest.fixture(scope="session")
def crossing(build_dir):
    return build(build_dir)
