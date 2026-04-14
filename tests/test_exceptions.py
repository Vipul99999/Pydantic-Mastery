"""Tests for structured error handling."""
import pytest

class TestExceptionFormatting:
    def test_validation_error_structure(self, client):
        payload = {"id": "not-an-int", "username": "u", "email": "invalid"}
        res = client.post("/api/lab/basics/user", json=payload)
        assert res.status_code == 422
        
        body = res.json()
        assert body["error"]["type"] == "validation_error"
        assert "field_errors" in body["error"]["details"]
        assert "request_id" in body["error"]
        assert "tips" in body["error"]["playground"]