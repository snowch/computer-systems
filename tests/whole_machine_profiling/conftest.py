"""The reader's profile reader, built once for the profiling chapter's three problems."""

from __future__ import annotations

import pytest

from tests.whole_machine_profiling.harness import build


@pytest.fixture(scope="session")
def profiler(build_dir):
    return build(build_dir)
