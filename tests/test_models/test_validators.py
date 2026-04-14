"""Tests for @field_validator and @model_validator."""
import pytest
from app.models.field_validators import FieldValidatorDemo
from app.models.model_validators import ModelValidatorDemo

class TestFieldValidators:
    def test_email_normalization(self):
        data = {"email": "  TEST@Example.COM  ", "tags": ["A", "a"], "age": 25, "username": "ok"}
        obj = FieldValidatorDemo(**data)
        assert obj.email == "test@example.com"

    def test_tag_deduplication(self):
        data = {"email": "t@e.com", "tags": ["py", "Py", "PYTHON", "fastapi"], "age": 20, "username": "u"}
        obj = FieldValidatorDemo(**data)
        assert len(obj.tags) <= 5
        assert len(obj.tags) == len(set(t.lower() for t in obj.tags))

    def test_age_wrap_validator(self):
        with pytest.raises(Exception, match="negative"):
            FieldValidatorDemo(email="e@e.com", tags=[], age=-1, username="u")

class TestModelValidators:
    def test_password_mismatch(self):
        with pytest.raises(Exception, match="match"):
            ModelValidatorDemo(
                username="u", email="e@e.com", 
                password="secret", confirm_password="different",
                subscription="free", is_premium=False, country="US", postal_code="10001"
            )

    def test_subscription_consistency(self):
        obj = ModelValidatorDemo(
            username="u", email="e@e.com",
            password="secure123", confirm_password="secure123",
            subscription="pro", is_premium=False, country="US", postal_code="10001"
        )
        assert obj.is_premium is True  # Auto-corrected by model_validator