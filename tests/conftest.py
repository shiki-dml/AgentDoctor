from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def contract2agent_test_root() -> Path:
    root = Path(__file__).resolve().parents[1] / ".tmp_pytest_base" / "contract2agent" / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    previous = os.environ.get("CONTRACT2AGENT_TEST_ROOT")
    os.environ["CONTRACT2AGENT_TEST_ROOT"] = str(root)
    try:
        yield root
    finally:
        if previous is None:
            os.environ.pop("CONTRACT2AGENT_TEST_ROOT", None)
        else:
            os.environ["CONTRACT2AGENT_TEST_ROOT"] = previous
        shutil.rmtree(root, ignore_errors=True)
