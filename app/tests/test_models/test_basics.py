"""Unit tests for basic Pydantic model validation."""
import pytest
from datetime import datetime
from app.models.basics import UserBasic, ConstraintExamples

class TestUserBasic:
    def test_valid_user(self):
        user = UserBasic(
            id=1, username="alice_dev", email="alice@example.com"
        )
        assert user.id == 1
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)

    def test_invalid_username(self):
        with pytest.raises(Exception) as exc:
            UserBasic(id=1, username="ab", email="a@b.com")
        assert "min_length" in str(exc.value).lower() or "short" in str(exc.value).lower()

    def test_invalid_email_pattern(self):
        with pytest.raises(Exception):
            UserBasic(id=1, username="valid", email="not-an-email")

    def test_model_dump_modes(self):
        user = UserBasic(id=1, username="u", email="u@e.com")
        py_dump = user.model_dump(mode="python")
        json_dump = user.model_dump(mode="json")
        assert isinstance(py_dump["created_at"], datetime)
        assert isinstance(json_dump["created_at"], str)