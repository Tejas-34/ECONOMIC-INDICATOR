import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Force mock mode for fast, deterministic unit test runs
os.environ["DATA_MODE"] = "mock"

from backend.app.main import app
from backend.app.security.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset slowapi rate limits before and after every test."""
    try:
        limiter.reset()
    except Exception:
        pass
    yield
    try:
        limiter.reset()
    except Exception:
        pass


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
