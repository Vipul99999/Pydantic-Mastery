"""Shared fixtures & configuration overrides for testing."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import AppSettings, settings as live_settings
import tempfile
import json

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for test environment."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        return AppSettings(
            environment="testing",
            debug=True,
            allowed_origins=[],
            database=type(live_settings.database)(
                data_path=tmp_path / "test_data.json",
                backup_path=tmp_path / "backups",
                auto_backup=False
            ),
            security=type(live_settings.security)()
        )

@pytest.fixture
def client(test_settings):
    """FastAPI TestClient with overridden settings."""
    app.state.settings = test_settings
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_user_payload():
    """Valid user payload for testing."""
    return {
        "id": 42,
        "username": "test_user",
        "email": "test@example.com",
        "role": "user",
        "is_active": True,
        "address": {"street": "123 Test St", "city": "QA City", "country": "US"}
    }