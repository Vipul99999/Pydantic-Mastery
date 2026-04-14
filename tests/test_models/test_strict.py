"""Tests for ConfigDict strict mode & alias generation."""
import pytest
from app.models.strict_config import StrictUser, LenientUser, CamelCaseModel

class TestStrictMode:
    def test_strict_rejects_string_int(self):
        with pytest.raises(Exception):
            StrictUser(id="123", username="u", email="e@e.com", age=25)

    def test_strict_forbids_extra_fields(self):
        with pytest.raises(Exception, match="extra"):
            StrictUser(id=1, username="u", email="e@e.com", age=25, unknown="x")

    def test_lenient_coerces_and_ignores(self):
        obj = LenientUser(id="42", username="u", email="e@e.com", age=25, typo="ignored")
        assert obj.id == 42  # Coerced
        assert not hasattr(obj, "typo")  # Ignored

class TestAliases:
    def test_camel_case_input_output(self):
        obj = CamelCaseModel(userId=1, firstName="Alice", lastName="Smith", emailAddress="a@e.com")
        dumped = obj.model_dump(by_alias=True)
        assert "userId" in dumped
        assert "firstName" in dumped